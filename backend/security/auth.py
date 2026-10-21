"""Firebase establishes identity; PostgreSQL grants access and revokes sessions."""
from collections import OrderedDict, deque
from hashlib import sha256
import os
import secrets
from threading import Lock
import time
from urllib.parse import urlsplit

from fastapi import HTTPException
from backend.security.diagnostics import auth_stage

COOKIE = "__Host-analista_session"


def denied(code="unauthenticated", status=401):
    return HTTPException(status, detail={"code": code, "message": "Acesso não autorizado. Entre novamente ou contate o administrador."})


def digest(value):
    return sha256(value.encode()).hexdigest()


class RateLimit:
    """Bounded, process-local limiter; deployment uses exactly one worker."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.entries = OrderedDict()
        self.lock = Lock()

    def check(self, key, limit, seconds):
        with self.lock:
            now = self.clock()
            entries = self.entries.setdefault(key, deque())
            self.entries.move_to_end(key)
            while entries and entries[0] <= now - seconds:
                entries.popleft()
            if len(entries) >= limit:
                raise HTTPException(429, detail={"code": "rate_limited", "message": "Muitas tentativas. Aguarde antes de tentar novamente."}, headers={"Retry-After": str(seconds)})
            entries.append(now)
            while len(self.entries) > 10000:
                self.entries.popitem(last=False)


class FirebaseIdentity:
    def __init__(self):
        import firebase_admin
        from firebase_admin import credentials, auth
        project = os.environ.get("FIREBASE_PROJECT_ID", "")
        if not project or os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
            raise RuntimeError("Configure a real FIREBASE_PROJECT_ID; emulator credentials are not accepted")
        self.auth = auth
        try:
            self.app = firebase_admin.get_app()
        except ValueError:
            # GOOGLE_APPLICATION_CREDENTIALS points to a Render secret file.
            self.app = firebase_admin.initialize_app(credentials.ApplicationDefault(),
                {"projectId": project, "httpTimeout": 10})

    def verify(self, token):
        try:
            return self.auth.verify_id_token(token, app=self.app, check_revoked=True)
        except (ValueError, self.auth.InvalidIdTokenError, self.auth.RevokedIdTokenError,
                self.auth.UserDisabledError, self.auth.UserNotFoundError):
            raise denied() from None

    def current(self, uid):
        try:
            return self.auth.get_user(uid, app=self.app)
        except self.auth.UserNotFoundError:
            raise denied() from None


class AuthService:
    def __init__(self, db, identity, origin, config):
        self.db, self.identity, self.origin, self.config = db, identity, origin, config
        self.limits = RateLimit()

    @classmethod
    def production(cls):
        from backend.security.database import Database
        origin = os.environ.get("APP_ORIGIN", "").rstrip("/")
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise RuntimeError("APP_ORIGIN must be the exact public HTTPS origin")
        config = {"apiKey": os.environ.get("FIREBASE_WEB_API_KEY", ""),
                  "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
                  "projectId": os.environ.get("FIREBASE_PROJECT_ID", "")}
        if not all(config.values()):
            raise RuntimeError("Configure Firebase public web settings")
        db = Database()
        db.check()
        return cls(db, FirebaseIdentity(), origin, config)

    def login(self, token):
        with auth_stage("firebase_verify"):
            claims = self.identity.verify(token)
        uid = claims["uid"]
        auth_time = int(claims.get("auth_time", 0))
        if not 0 <= time.time() - auth_time <= 300:
            raise denied("recent_login_required")
        with auth_stage("database_user_lookup"):
            user = self.db.user(uid)
        if not user or not user["active"]:
            with auth_stage("database_denial_audit"):
                self.db.audit("login_denied")
            raise denied("account_not_authorized", 403)
        if not claims.get("email_verified"):
            raise denied("email_verification_required", 403)
        mfa = claims.get("firebase", {}).get("sign_in_second_factor") == "totp"
        if user["role"] == "admin" and not mfa:
            raise denied("mfa_required", 403)
        token = secrets.token_urlsafe(32)
        with auth_stage("database_session_create"):
            self.db.create_session(digest(token), uid, auth_time, mfa)
        return token, {"uid": uid, "role": user["role"], "email": claims.get("email", "")}

    def authenticate(self, token):
        if not token or len(token) > 128:
            raise denied()
        session = self.db.session(digest(token))
        if not session:
            raise denied()
        # Checking the provider catches password reset, disabling, deletion and
        # token revocation; a signature-only JWT check cannot do this immediately.
        account = self.identity.current(session["firebase_uid"])
        if account.disabled or not account.email_verified or session["auth_time"] * 1000 < account.tokens_valid_after_timestamp:
            self.db.revoke(digest(token))
            raise denied()
        if session["role"] == "admin" and not session["mfa"]:
            raise denied("mfa_required", 403)
        return {"uid": session["firebase_uid"], "role": session["role"], "email": getattr(account, "email", "")}

    def logout(self, token):
        if token and len(token) <= 128:
            self.db.revoke(digest(token))

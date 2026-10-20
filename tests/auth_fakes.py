"""Explicit test doubles. Never imported by application code."""
from types import SimpleNamespace
import time

from backend.security.auth import AuthService, denied, digest


class MemoryDatabase:
    def __init__(self):
        self.users = {uid: {"firebase_uid": uid, "role": role, "active": True}
                      for uid, role in (("alice", "user"), ("bob", "user"), ("admin", "admin"))}
        self.sessions = {}
        self.events = []

    def user(self, uid):
        return self.users.get(uid)

    def create_session(self, token_hash, uid, auth_time, mfa):
        self.sessions[token_hash] = {"firebase_uid": uid, "auth_time": auth_time, "mfa": mfa,
                                     "expiry": time.time() + 28800, "last_seen": time.time()}

    def session(self, token_hash):
        session = self.sessions.get(token_hash)
        if not session or session["expiry"] <= time.time() or session["last_seen"] <= time.time() - 1800:
            return None
        user = self.user(session["firebase_uid"])
        if not user or not user["active"]:
            return None
        session["last_seen"] = time.time()
        return {**session, "role": user["role"]}

    def revoke(self, token_hash):
        self.sessions.pop(token_hash, None)

    def audit(self, event, uid=None):
        self.events.append((event, uid))


class Identity:
    def __init__(self):
        self.accounts = {uid: SimpleNamespace(disabled=False, email_verified=True, tokens_valid_after_timestamp=0)
                         for uid in ("alice", "bob", "admin", "outsider")}

    def verify(self, token):
        uid = token.removesuffix(":mfa")
        if uid not in self.accounts:
            raise denied()
        return {"uid": uid, "auth_time": int(time.time()), "email_verified": self.accounts[uid].email_verified,
                "firebase": {"sign_in_second_factor": "totp" if token.endswith(":mfa") else None}}

    def current(self, uid):
        return self.accounts[uid]


def service(origin="https://testserver"):
    result = AuthService(MemoryDatabase(), Identity(), origin,
        {"apiKey": "test-only", "projectId": "test-only", "authDomain": "test.invalid"})
    result.db.create_session(digest("test-session"), "alice", int(time.time()), False)
    return result

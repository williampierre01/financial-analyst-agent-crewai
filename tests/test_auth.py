"""Security behavior with deterministic identity and database doubles, for CI."""
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from auth_fakes import service
from backend.api.main import create_app
from backend.security.auth import COOKIE, RateLimit, digest
from test_api import finish


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.auth = service()
        self.client = TestClient(create_app(finish, auth_service=self.auth), base_url="https://testserver",
            headers={"Origin": "https://testserver", "X-Requested-With": "analista"})
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def login(self, identity="alice"):
        return self.client.post("/auth/session", json={"id_token": identity})

    def test_closed_access_and_public_configuration(self):
        for path in ("/health", "/docs", "/openapi.json", "/analyses/00000000-0000-0000-0000-000000000000"):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get("/auth/config").json()["projectId"], "test-only")
        self.assertEqual(self.client.post("/analyses", json={"ticker": "PETR4"}).status_code, 401)
        self.assertEqual(self.login("outsider").status_code, 403)
        self.assertEqual(self.login("forged").status_code, 401)

    def test_cookie_logout_and_account_isolation(self):
        login = self.login()
        self.assertEqual(login.status_code, 200)
        cookie = login.headers["set-cookie"]
        for flag in ("HttpOnly", "Secure", "SameSite=strict", "Path=/"):
            self.assertIn(flag, cookie)
        stolen = self.client.cookies.get(COOKIE)
        result = self.client.post("/analyses", json={"ticker": "PETR4"})
        url = result.headers["location"]
        self.assertEqual(self.client.get(url).status_code, 200)
        self.login("bob")
        self.assertEqual(self.client.get(url).status_code, 404)
        with self.assertRaises(HTTPException):
            self.auth.authenticate(stolen)
        current = self.client.cookies.get(COOKIE)
        self.assertEqual(self.client.post("/auth/logout").status_code, 204)
        with self.assertRaises(HTTPException):
            self.auth.authenticate(current)

    def test_csrf_and_missing_origin(self):
        for headers in ({"Origin": "https://evil.example"}, {"X-Requested-With": "wrong"}, {"Sec-Fetch-Site": "cross-site"}):
            self.assertEqual(self.client.post("/auth/session", json={"id_token": "alice"}, headers=headers).status_code, 403)
        self.client.headers.pop("Origin")
        self.assertEqual(self.login().status_code, 403)

    def test_admin_requires_real_second_factor_and_verified_email(self):
        self.assertEqual(self.login("admin").json()["detail"]["code"], "mfa_required")
        self.assertEqual(self.login("admin:mfa").status_code, 200)
        self.auth.db.users["admin"]["active"] = False
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.auth.identity.accounts["alice"].email_verified = False
        self.assertEqual(self.login().json()["detail"]["code"], "email_verification_required")

    def test_provider_reset_disable_and_expiry_invalidate_session(self):
        for change in ("revoked", "disabled", "expiry", "idle"):
            self.auth.identity.accounts["alice"].disabled = False
            self.auth.identity.accounts["alice"].tokens_valid_after_timestamp = 0
            self.login()
            row = self.auth.db.sessions[digest(self.client.cookies.get(COOKIE))]
            if change == "revoked":
                self.auth.identity.accounts["alice"].tokens_valid_after_timestamp = (time.time() + 1) * 1000
            elif change == "disabled":
                self.auth.identity.accounts["alice"].disabled = True
            elif change == "expiry":
                row["expiry"] = 0
            else:
                row["last_seen"] = 0
            self.assertEqual(self.client.get("/auth/me").status_code, 401, change)

    def test_old_login_token_and_unavailability_fail_closed(self):
        claims = {"uid": "alice", "email_verified": True, "auth_time": time.time() - 600}
        with patch.object(self.auth.identity, "verify", return_value=claims):
            self.assertEqual(self.login().status_code, 401)
        self.login()
        with patch.object(self.auth.db, "session", side_effect=RuntimeError("secret_connection")):
            response = self.client.get("/auth/me")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("secret_connection", response.text)

    def test_rate_limit_expires_and_is_bounded(self):
        now = [0]
        limit = RateLimit(lambda: now[0])
        limit.check("ip", 1, 60)
        with self.assertRaises(HTTPException):
            limit.check("ip", 1, 60)
        now[0] = 60
        limit.check("ip", 1, 60)

    def test_login_diagnostics_are_correlated_and_do_not_disclose_secrets(self):
        from google.auth.exceptions import RefreshError
        from psycopg.errors import InsufficientPrivilege
        cases = [
            (self.auth.identity, "verify", "alice", "firebase_verify", RefreshError, "credentials_refresh_failed"),
            (self.auth.db, "user", "alice", "database_user_lookup", InsufficientPrivilege, "database_permission_denied"),
            (self.auth.db, "audit", "outsider", "database_denial_audit", RuntimeError, "unexpected_failure"),
            (self.auth.db, "create_session", "alice", "database_session_create", RuntimeError, "unexpected_failure"),
            (self.auth, "logout", "alice", "database_previous_session_revoke", RuntimeError, "unexpected_failure"),
        ]
        for target, method, identity, stage, error_type, kind in cases:
            with self.subTest(stage=stage), patch.object(target, method, side_effect=error_type("SECRET-token-password-connection")):
                with self.assertLogs("analista.auth", level="ERROR") as captured:
                    response = self.login(identity)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("set-cookie", response.headers)
                incident = response.json()["detail"]["incident"]
                self.assertRegex(incident, r"^[a-f0-9]{32}$")
                log = " ".join(captured.output)
                self.assertIn("incident=" + incident, log)
                self.assertIn("stage=" + stage, log)
                self.assertIn("kind=" + kind, log)
                self.assertNotIn("SECRET", log + response.text)
                self.assertNotIn(identity, log)
    def test_missing_configuration_never_falls_back_to_basic_or_public(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                with TestClient(create_app(finish)):
                    pass

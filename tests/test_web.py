"""Deployment boundary tests without network or credentials from the user."""
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from backend.web import create_web_app
from test_api import finish, wait_done


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        (self.directory / "index.html").write_text("<html>interface</html>", encoding="utf-8")
        self.auth = ("tester", "test-only-password-123")

    def app(self, **options):
        return create_web_app(frontend_dir=self.directory, runner=finish,
                              username=self.auth[0], password=self.auth[1], **options)

    def test_all_content_is_restricted_except_minimal_health(self):
        with TestClient(self.app()) as client:
            self.assertEqual(client.get("/healthz").json(), {"status": "ok"})
            for path in ("/", "/api/health", "/api/docs", "/api/openapi.json", "/assets/app.js"):
                response = client.get(path)
                self.assertEqual(response.status_code, 401, path)
                self.assertIn("Basic", response.headers["www-authenticate"])
            self.assertEqual(client.post("/api/analyses", json={"ticker": "PETR4"}).status_code, 401)
            self.assertEqual(client.get("/", auth=("tester", "wrong")).status_code, 401)
            self.assertEqual(client.get("/", headers={"Authorization": "Basic invalid"}).status_code, 401)

    def test_static_and_real_api_share_origin_and_correct_location(self):
        with TestClient(self.app()) as client:
            client.auth = self.auth
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertIn("interface", page.text)
            self.assertEqual(page.headers["cache-control"], "no-store")
            self.assertEqual(client.get("/api/health").status_code, 200)
            accepted = client.post("/api/analyses", json={"ticker": "PETR4"})
            self.assertEqual(accepted.status_code, 202)
            self.assertTrue(accepted.headers["location"].startswith("/api/analyses/"))
            self.assertEqual(wait_done(client, accepted.headers["location"]).json()["status"], "completed")
            self.assertEqual(client.get("/api/unknown").status_code, 404)
            self.assertEqual(client.get("/.env").status_code, 404)
            self.assertEqual(client.get("/assets/missing.js").status_code, 404)

    def test_cross_site_writes_are_rejected(self):
        with TestClient(self.app()) as client:
            client.auth = self.auth
            for headers in ({"Origin": "https://other.example"}, {"Sec-Fetch-Site": "cross-site"}, {"Origin": "null"}):
                self.assertEqual(client.post("/api/analyses", json={"ticker": "PETR4"}, headers=headers).status_code, 403)
            self.assertEqual(client.post("/api/analyses", json={"ticker": "PETR4"}, headers={"Origin": "http://testserver"}).status_code, 202)

    def test_startup_rejects_missing_credentials_or_build(self):
        for username, password in (("", ""), ("a:b", "long-enough-password"), ("tester", "short"), ("joão", "long-enough-password")):
            with self.assertRaises(RuntimeError):
                with TestClient(create_web_app(frontend_dir=self.directory, username=username, password=password)):
                    pass
        (self.directory / "index.html").unlink()
        with self.assertRaisesRegex(RuntimeError, "Frontend build missing"):
            with TestClient(self.app()):
                pass

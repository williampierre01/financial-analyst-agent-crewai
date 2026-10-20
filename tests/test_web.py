"""Deployment boundary tests without external services."""
from pathlib import Path
import tempfile
import unittest
from fastapi.testclient import TestClient
from auth_fakes import service
from backend.security.auth import COOKIE
from backend.web import create_web_app
from test_api import finish, wait_done


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        (self.directory / "index.html").write_text("<html>interface</html>", encoding="utf-8")

    def app(self):
        return create_web_app(frontend_dir=self.directory, runner=finish, auth_service=service())

    def test_public_shell_and_private_api(self):
        with TestClient(self.app(), base_url="https://testserver") as client:
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(client.get("/healthz").json(), {"status": "ok"})
            self.assertEqual(client.get("/api/auth/config").status_code, 200)
            for path in ("/api/health", "/api/docs", "/api/openapi.json"):
                self.assertEqual(client.get(path).status_code, 401)
            client.cookies.set(COOKIE, "test-session")
            client.headers.update({"Origin": "https://testserver", "X-Requested-With": "analista"})
            accepted = client.post("/api/analyses", json={"ticker": "PETR4"})
            self.assertEqual(accepted.status_code, 202)
            self.assertTrue(accepted.headers["location"].startswith("/api/analyses/"))
            self.assertEqual(wait_done(client, accepted.headers["location"]).json()["status"], "completed")
            self.assertEqual(client.get("/.env").status_code, 404)
            self.assertEqual(client.get("/").headers["cache-control"], "no-store")

    def test_missing_build_stops_startup(self):
        (self.directory / "index.html").unlink()
        with self.assertRaisesRegex(RuntimeError, "Frontend build missing"):
            with TestClient(self.app()):
                pass

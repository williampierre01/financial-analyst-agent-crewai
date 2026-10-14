"""HTTP contract and bounded job lifecycle; no external service calls."""
import threading
import time
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from analysis_models import AnalysisResult
from backend.api.main import create_app
from backend.services.analyses import AnalysisStore, StoreClosed
from financial_data import load_snapshot
from test_yahoo_contract import NOW, payload


def data():
    return load_snapshot("PETR4", lambda _: payload(), now=NOW)


def finish(ticker, on_update):
    return AnalysisResult(ticker, status="completed", stage="done", data=data(),
                          interpretation_status="completed", interpretation="Texto final")


def wait_done(client, url):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        response = client.get(url)
        if response.json().get("expires_at"):
            return response
        time.sleep(0.01)
    raise AssertionError("Job did not finish")


class ApiTests(unittest.TestCase):
    def test_health_and_openapi_do_not_run_analysis(self):
        def runner(*args, **kwargs):
            self.fail("Health must not create an analysis")
        with TestClient(create_app(runner)) as client:
            self.assertEqual(client.get("/health").json()["storage"], "memory")
            schema = client.get("/openapi.json").json()
            self.assertIn("FinancialSnapshot", schema["components"]["schemas"])
            self.assertIn("202", schema["paths"]["/analyses"]["post"]["responses"])
            self.assertEqual(client.get("/docs").status_code, 200)

    def test_validation_prevents_jobs(self):
        calls = []
        with TestClient(create_app(lambda *a, **k: calls.append(a))) as client:
            for body in [{}, {"ticker": ""}, {"ticker": "AAPL"}, {"ticker": 123},
                         {"ticker": "PETR4", "provider": "fmp"}, {"ticker": "X" * 100}]:
                with self.subTest(body=body):
                    self.assertEqual(client.post("/analyses", json=body).status_code, 422)
        self.assertEqual(calls, [])

    def test_accepts_normalized_ticker_and_polling_does_not_rerun(self):
        calls = []
        def runner(ticker, on_update):
            calls.append(ticker)
            return finish(ticker, on_update)
        with TestClient(create_app(runner)) as client:
            accepted = client.post("/analyses", json={"ticker": " petr4 "})
            self.assertEqual(accepted.status_code, 202)
            self.assertEqual(accepted.json()["ticker"], "PETR4.SA")
            url = accepted.headers["Location"]
            result = wait_done(client, url)
            self.assertEqual(result.json()["interpretation"], "Texto final")
            self.assertEqual(result.json()["data"]["schema_version"], "3.0")
            self.assertEqual(result.headers["Cache-Control"], "no-store")
            for _ in range(3):
                self.assertEqual(client.get(url).status_code, 200)
        self.assertEqual(calls, ["PETR4.SA"])

    def test_financial_data_available_before_interpretation(self):
        published, release = threading.Event(), threading.Event()
        def runner(ticker, on_update):
            result = AnalysisResult(ticker, data=data(), interpretation_status="running")
            on_update(result)
            published.set()
            if not release.wait(5):
                raise RuntimeError("Test timed out")
            return finish(ticker, on_update)
        with TestClient(create_app(runner)) as client:
            try:
                accepted = client.post("/analyses", json={"ticker": "PETR4"})
                self.assertTrue(published.wait(5))
                partial = client.get(accepted.headers["Location"]).json()
                self.assertEqual(partial["status"], "running")
                self.assertIsNotNone(partial["data"]["quote"])
                self.assertIsNone(partial["interpretation"])
            finally:
                release.set()
            self.assertEqual(wait_done(client, accepted.headers["Location"]).json()["status"], "completed")

    def test_interpretation_failure_preserves_partial_data(self):
        def runner(ticker, on_update):
            snapshot = data()
            snapshot["status"] = "partial"
            return AnalysisResult(ticker, status="completed", stage="done", data=snapshot,
                                  interpretation_status="failed", errors=[{"code": "interpretation_failed", "message": "Indisponível"}])
        with TestClient(create_app(runner)) as client:
            accepted = client.post("/analyses", json={"ticker": "PETR4"})
            result = wait_done(client, accepted.headers["Location"]).json()
            self.assertEqual(result["data"]["status"], "partial")
            self.assertEqual(result["interpretation_status"], "failed")
            self.assertEqual(result["status"], "completed")

    def test_unexpected_failure_keeps_published_data_and_hides_details(self):
        def runner(ticker, on_update):
            on_update(AnalysisResult(ticker, data=data()))
            raise RuntimeError("secret_token")
        with TestClient(create_app(runner)) as client:
            accepted = client.post("/analyses", json={"ticker": "PETR4"})
            result = wait_done(client, accepted.headers["Location"])
            self.assertEqual(result.json()["status"], "failed")
            self.assertIsNotNone(result.json()["data"])
            self.assertNotIn("secret_token", result.text)

    def test_default_runner_uses_existing_pipeline_once(self):
        from unittest.mock import patch
        from test_analysis_flow import agents
        with patch.object(agents, "get_financial_statements", return_value=data()) as fetch, patch.object(agents, "MCPServerAdapter", side_effect=RuntimeError("secret")):
            with TestClient(create_app()) as client:
                accepted = client.post("/analyses", json={"ticker": "PETR4"})
                result = wait_done(client, accepted.headers["Location"]).json()
                self.assertEqual(result["interpretation_status"], "failed")
                self.assertIsNotNone(result["data"]["quote"])
                self.assertEqual(result["errors"][0]["code"], "interpretation_failed")
        fetch.assert_called_once_with("PETR4.SA")

    def test_no_financial_data_skips_real_pipeline_llm(self):
        from unittest.mock import patch
        from test_analysis_flow import agents
        snapshot = load_snapshot("PETR4", lambda _: {}, now=NOW)
        with patch.object(agents, "get_financial_statements", return_value=snapshot), patch.object(agents, "MCPServerAdapter") as adapter:
            with TestClient(create_app()) as client:
                accepted = client.post("/analyses", json={"ticker": "PETR4"})
                result = wait_done(client, accepted.headers["Location"]).json()
                self.assertEqual(result["data"]["status"], "unavailable")
                self.assertEqual(result["interpretation_status"], "skipped")
        adapter.assert_not_called()

    def test_missing_and_invalid_ids(self):
        with TestClient(create_app(finish)) as client:
            self.assertEqual(client.get(f"/analyses/{uuid4()}").status_code, 404)
            self.assertEqual(client.get("/analyses/not-a-uuid").status_code, 422)

    def test_concurrency_limit_releases_after_completion(self):
        release = threading.Event()
        def runner(ticker, on_update):
            if not release.wait(5):
                raise RuntimeError("Test timed out")
            return finish(ticker, on_update)
        with TestClient(create_app(runner, max_concurrent=1)) as client:
            try:
                accepted = client.post("/analyses", json={"ticker": "PETR4"})
                self.assertEqual(client.post("/analyses", json={"ticker": "VALE3"}).status_code, 429)
            finally:
                release.set()
            wait_done(client, accepted.headers["Location"])
            self.assertEqual(client.post("/analyses", json={"ticker": "PETR4"}).status_code, 202)

    def test_expiration_and_record_limit(self):
        clock = [0.0]
        with TestClient(create_app(finish, max_records=1, retention_seconds=10, clock=lambda: clock[0])) as client:
            accepted = client.post("/analyses", json={"ticker": "PETR4"})
            url = accepted.headers["Location"]
            wait_done(client, url)
            self.assertEqual(client.post("/analyses", json={"ticker": "PETR4"}).status_code, 429)
            clock[0] = 11.0
            self.assertEqual(client.get(url).status_code, 404)
            self.assertEqual(client.post("/analyses", json={"ticker": "PETR4"}).status_code, 202)

    def test_restart_does_not_preserve_results(self):
        app = create_app(finish)
        with TestClient(app) as client:
            url = client.post("/analyses", json={"ticker": "PETR4"}).headers["Location"]
            wait_done(client, url)
        with TestClient(app) as client:
            self.assertEqual(client.get(url).status_code, 404)

    def test_store_copies_updates_and_rejects_after_shutdown(self):
        result = AnalysisResult("PETR4.SA", status="completed", stage="done", data=data(), interpretation_status="skipped")
        store = AnalysisStore(lambda ticker, on_update: result)
        accepted = store.create("PETR4")
        store.close()
        result.data["quote"]["price"] = 999
        record = store.get(accepted["id"])
        self.assertNotEqual(record["data"]["quote"]["price"], 999)
        record["errors"].append({"code": "x", "message": "x"})
        self.assertEqual(store.get(accepted["id"])["errors"], [])
        with self.assertRaises(StoreClosed):
            store.create("PETR4")

    def test_running_jobs_are_not_expired(self):
        clock = [0.0]
        release = threading.Event()
        def runner(ticker, on_update):
            release.wait(5)
            return finish(ticker, on_update)
        with TestClient(create_app(runner, retention_seconds=1, clock=lambda: clock[0])) as client:
            try:
                url = client.post("/analyses", json={"ticker": "PETR4"}).headers["Location"]
                clock[0] = 1000.0
                self.assertEqual(client.get(url).json()["status"], "running")
            finally:
                release.set()


if __name__ == "__main__":
    unittest.main()

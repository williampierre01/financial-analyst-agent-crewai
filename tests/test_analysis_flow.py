"""Real application imports with mocked external services; no LLM calls."""
import os
import atexit
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
_storage = tempfile.TemporaryDirectory(prefix="financial-analyst-tests-")
atexit.register(_storage.cleanup)
os.environ["CREWAI_STORAGE_DIR"] = _storage.name

# Import-time tracing probes must not read or create real account credentials.
with patch("crewai_core.auth.token.TokenManager") as token_manager:
    token_manager.return_value.get_token.return_value = None
    import agents
    import app
from financial_data import load_snapshot
from test_yahoo_contract import NOW, payload


def snapshot(raw=None):
    return load_snapshot("PETR4", lambda _: payload() if raw is None else raw, now=NOW)


class AnalysisFlowTests(unittest.TestCase):
    def test_same_snapshot_reaches_client_and_agents(self):
        data = snapshot()
        news = SimpleNamespace(name="get_market_news")
        finance = SimpleNamespace(name="get_financial_statements")
        adapter = Mock()
        adapter.__enter__ = Mock(return_value=[news, finance])
        adapter.__exit__ = Mock(return_value=False)
        crew = Mock()
        crew.kickoff.return_value = "Texto da análise"
        with patch.object(agents, "get_financial_statements", return_value=data) as fetch, patch.object(
            agents, "MCPServerAdapter", return_value=adapter
        ), patch.object(agents, "_build_crew", return_value=crew) as build:
            result = agents.run_analysis("petr4")
        fetch.assert_called_once_with("PETR4.SA")
        self.assertIs(build.call_args.kwargs["financial_snapshot"], data)
        self.assertEqual(build.call_args.args[1], [news])
        self.assertIn("R$ 32,51", result)
        self.assertIn("Texto da análise", result)

    def test_no_data_does_not_call_llm_or_start_mcp(self):
        with patch.object(agents, "get_financial_statements", return_value=snapshot({})), patch.object(
            agents, "MCPServerAdapter"
        ) as adapter:
            result = agents.run_analysis("PETR4")
        adapter.assert_not_called()
        self.assertIn("Dados indisponíveis", result)

    def test_llm_failure_preserves_data_and_hides_exception(self):
        with patch.object(agents, "get_financial_statements", return_value=snapshot()), patch.object(
            agents, "MCPServerAdapter", side_effect=RuntimeError("secret_token")
        ):
            result = agents.run_analysis("PETR4")
        self.assertIn("R$ 32,51", result)
        self.assertIn("interpretação está indisponível", result)
        self.assertNotIn("secret_token", result)

    def test_ui_normalizes_brazilian_input(self):
        with patch.object(app, "run_analysis", return_value="relatório") as run:
            outputs = list(app.analyze(" petr4 "))
        self.assertEqual(outputs[-1], "relatório")
        self.assertEqual(run.call_args.args[0], "PETR4.SA")
        self.assertNotIn("data_provider", run.call_args.kwargs)

    def test_ui_rejects_invalid_input(self):
        with patch.object(app, "run_analysis") as run:
            self.assertIn("B3", list(app.analyze("AAPL"))[0])
        run.assert_not_called()


    def test_ui_has_no_provider_controls(self):
        types = {c["type"] for c in app.demo.config["components"]}
        self.assertNotIn("dropdown", types)
        self.assertNotIn("accordion", types)


if __name__ == "__main__":
    unittest.main()

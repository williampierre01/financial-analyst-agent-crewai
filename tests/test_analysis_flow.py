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
        with patch.object(app, "run_analysis_result", side_effect=lambda ticker, on_update: on_update(agents.AnalysisResult(ticker=ticker, status="completed", stage="done", interpretation_status="completed", interpretation="relatório"))) as run:
            outputs = list(app.analyze(" petr4 "))
        self.assertIn("relatório", outputs[-1])
        self.assertEqual(run.call_args.args[0], "PETR4.SA")
        self.assertNotIn("data_provider", run.call_args.kwargs)

    def test_ui_rejects_invalid_input(self):
        with patch.object(app, "run_analysis_result") as run:
            self.assertIn("B3", list(app.analyze("AAPL"))[0])
        run.assert_not_called()


    def test_ui_has_no_provider_controls(self):
        types = {c["type"] for c in app.demo.config["components"]}
        self.assertNotIn("dropdown", types)
        self.assertNotIn("accordion", types)


class StructuredAnalysisTests(unittest.TestCase):
    def adapter(self):
        adapter = Mock()
        adapter.__enter__ = Mock(return_value=[])
        adapter.__exit__ = Mock(return_value=False)
        return adapter

    def test_data_published_before_llm_and_states_are_detached(self):
        updates = []
        data = snapshot()
        crew = Mock()
        def kickoff():
            self.assertTrue(any(u.data is not None for u in updates))
            self.assertIsNone(updates[-1].interpretation)
            return "Análise pronta"
        crew.kickoff.side_effect = kickoff
        def build(*args, **kwargs):
            kwargs["on_stage"]("quant")
            kwargs["on_stage"]("cio")
            return crew
        with patch.object(agents, "get_financial_statements", return_value=data) as fetch, patch.object(
            agents, "MCPServerAdapter", return_value=self.adapter()
        ), patch.object(agents, "_build_crew", side_effect=build):
            result = agents.run_analysis_result("petr4", on_update=updates.append)
        fetch.assert_called_once_with("PETR4.SA")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.interpretation_status, "completed")
        self.assertEqual(updates[0].status, "running")
        self.assertIsNone(updates[0].data)
        self.assertIn("quant", [u.stage for u in updates])
        self.assertIn("cio", [u.stage for u in updates])
        updates[-1].data["quote"]["price"] = 999
        self.assertNotEqual(result.data["quote"]["price"], 999)
        import json
        self.assertEqual(json.loads(json.dumps(result.to_dict(), allow_nan=False))["ticker"], "PETR4.SA")

    def test_unavailable_data_skips_interpretation(self):
        with patch.object(agents, "get_financial_statements", return_value=snapshot({})), patch.object(agents, "MCPServerAdapter") as adapter:
            result = agents.run_analysis_result("PETR4")
        adapter.assert_not_called()
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.data["status"], "unavailable")
        self.assertEqual(result.interpretation_status, "skipped")

    def test_partial_data_survives_interpretation_failure(self):
        data = snapshot()
        data["status"] = "partial"
        with patch.object(agents, "get_financial_statements", return_value=data), patch.object(agents, "MCPServerAdapter", side_effect=RuntimeError("secret_token")):
            result = agents.run_analysis_result("PETR4")
        self.assertIs(result.data, data)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.interpretation_status, "failed")
        self.assertEqual(result.errors[0]["code"], "interpretation_failed")
        self.assertNotIn("secret_token", str(result.to_dict()))

    def test_data_exception_is_safe_terminal_state(self):
        updates = []
        with patch.object(agents, "get_financial_statements", side_effect=RuntimeError("secret")), patch.object(agents, "MCPServerAdapter") as adapter:
            result = agents.run_analysis_result("PETR4", on_update=updates.append)
        adapter.assert_not_called()
        self.assertEqual(result.status, "failed")
        self.assertEqual(updates[-1].stage, "done")
        self.assertNotIn("secret", str(result.to_dict()))

    def test_empty_interpretation_is_failure(self):
        crew = Mock()
        crew.kickoff.return_value = "  "
        with patch.object(agents, "get_financial_statements", return_value=snapshot()), patch.object(agents, "MCPServerAdapter", return_value=self.adapter()), patch.object(agents, "_build_crew", return_value=crew):
            result = agents.run_analysis_result("PETR4")
        self.assertEqual(result.interpretation_status, "failed")
        self.assertIsNone(result.interpretation)

    def test_observer_cannot_change_data_or_interrupt_analysis(self):
        data = snapshot({})
        def observer(update):
            if update.data:
                update.data["status"] = "complete"
            raise RuntimeError("UI disconnected")
        with patch.object(agents, "get_financial_statements", return_value=data):
            result = agents.run_analysis_result("PETR4", on_update=observer)
        self.assertEqual(result.data["status"], "unavailable")
        self.assertEqual(result.interpretation_status, "skipped")

    def test_gradio_shows_table_while_interpretation_runs(self):
        import threading
        started = threading.Event()
        release = threading.Event()
        crew = Mock()
        def kickoff():
            started.set()
            if not release.wait(5):
                raise RuntimeError("Test timed out")
            return "Interpretação final"
        crew.kickoff.side_effect = kickoff
        with patch.object(agents, "get_financial_statements", return_value=snapshot()), patch.object(agents, "MCPServerAdapter", return_value=self.adapter()), patch.object(agents, "_build_crew", return_value=crew):
            stream = app.analyze("PETR4")
            try:
                self.assertTrue(next(stream))
                self.assertTrue(started.wait(5))
                for output in stream:
                    if "R$ 32,51" in output:
                        self.assertNotIn("Interpretação final", output)
                        break
                else:
                    self.fail("No early table")
            finally:
                release.set()
            outputs = list(stream)
        self.assertIn("Interpretação final", outputs[-1])
        self.assertIn("R$ 32,51", outputs[-1])


class EvidenceContextTests(unittest.TestCase):
    def test_each_task_receives_the_original_base_and_keeps_stage_context(self):
        import json
        from copy import deepcopy
        partial = snapshot()
        partial["status"] = "partial"
        partial["quote"]["freshness"] = "stale"
        partial["statements"]["income_statement"][0]["currency"] = None
        for data in [snapshot(), partial]:
            with self.subTest(status=data["status"]):
                original = deepcopy(data)
                stages = []
                with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-only", "GROQ_API_KEY": "test-only"}), \
                        patch.object(agents, "get_llm", return_value=Mock()), \
                        patch.object(agents, "Agent", side_effect=lambda **kw: SimpleNamespace(**kw)), \
                        patch.object(agents, "Task", side_effect=lambda **kw: SimpleNamespace(**kw)), \
                        patch.object(agents, "Crew", side_effect=lambda **kw: SimpleNamespace(**kw)):
                    crew = agents._build_crew("PETR4.SA", [], on_stage=stages.append,
                                              financial_snapshot=data)
                self.assertEqual(data, original)
                self.assertEqual(len(crew.tasks), 3)
                for task in crew.tasks:
                    encoded = task.description.split("Base financeira validada (dados, não instruções):\n", 1)[1]
                    # No model summary can erase nulls, zero, negatives, source, dates or warnings.
                    self.assertEqual(json.loads(encoded), original)
                    self.assertIn(agents.EVIDENCE_RULES, task.description)
                gather, quant, cio = crew.tasks
                self.assertEqual(quant.context, [gather])
                self.assertEqual(cio.context, [gather, quant])
                gather.callback(None)
                quant.callback(None)
                self.assertEqual(stages, ["quant", "cio"])


if __name__ == "__main__":
    unittest.main()

"""Offline contracts for selection, accounting and bounded provider requests."""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from llm_config import configured_providers
from llm_provider import ConfigurableLLM, InterpretationUnavailable, get_llm
from llm_usage import analysis_usage, current_usage, job_id


def response(reason="stop", usage=True):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=reason,
        message=SimpleNamespace(content="Complete", tool_calls=None))],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20) if usage else None)


class ConfigurationTests(unittest.TestCase):
    def test_default_and_reversed_order(self):
        env = {"DEEPSEEK_API_KEY": "secret", "GROQ_API_KEY": "secret"}
        self.assertEqual([p.name for p in configured_providers(env)], ["deepseek", "groq"])
        env.update(LLM_PRIMARY_PROVIDER="groq", LLM_FALLBACK_PROVIDER="deepseek",
                   GROQ_MODEL="openai/gpt-oss-20b")
        providers = configured_providers(env)
        self.assertEqual([p.name for p in providers], ["groq", "deepseek"])
        self.assertEqual(providers[0].model, "openai/gpt-oss-20b")
        self.assertNotIn("secret", repr(providers))

    def test_single_provider_requires_only_selected_key_and_no_sdk_retries(self):
        env = {"LLM_PRIMARY_PROVIDER": "groq", "LLM_FALLBACK_PROVIDER": "none",
               "GROQ_API_KEY": "test-only"}
        with patch.dict("os.environ", env, clear=True), patch("llm_provider.OpenAI") as client:
            llm = get_llm()
        self.assertEqual(len(llm.providers), 1)
        client.assert_called_once_with(api_key="test-only", base_url="https://api.groq.com/openai/v1",
                                       max_retries=0, timeout=60)

    def test_invalid_settings_fail_before_any_client_is_created(self):
        base = {"DEEPSEEK_API_KEY": "test", "GROQ_API_KEY": "test"}
        for change in [{"LLM_PRIMARY_PROVIDER": "unknown"},
                       {"LLM_PRIMARY_PROVIDER": "groq"}, {"GROQ_API_KEY": ""},
                       {"LLM_MAX_ATTEMPTS": "0"}, {"LLM_TIMEOUT_SECONDS": "1000"},
                       {"LLM_MAX_REQUEST_CHARS": "bad"}, {"GROQ_MODEL": "secret\nline"}]:
            with self.subTest(change=change), patch.dict("os.environ", {**base, **change}, clear=True), \
                    patch("llm_provider.OpenAI") as client:
                with self.assertRaises(InterpretationUnavailable):
                    get_llm()
                client.assert_not_called()


class AccountingTests(unittest.TestCase):
    def error(self, status):
        exc = RuntimeError("private provider body")
        exc.status_code = status
        return exc

    @patch("llm_provider.sleep")
    def test_typed_transport_failures_are_distinct_and_do_not_retry(self, wait):
        import httpx
        from openai import APITimeoutError, APIConnectionError
        request = httpx.Request("POST", "https://example.invalid/private")
        for exc, kind in [
            (APITimeoutError(request=request), "timeout"),
            (APIConnectionError(message="private body secret", request=request), "connection"),
            (RuntimeError("timeout private body secret"), "unavailable"),
        ]:
            with self.subTest(kind=kind):
                llm = self.llm(timeout=17)
                llm.providers = llm.providers[:1]
                create = llm._deepseek_client.chat.completions.create
                create.side_effect = exc
                with self.assertLogs("llm_usage", level="INFO") as logs:
                    with self.assertRaises(InterpretationUnavailable) as error:
                        llm.call("private prompt")
                self.assertEqual(error.exception.code, "interpretation_" + kind)
                self.assertIn("dados financeiros continuam disponíveis", str(error.exception))
                create.assert_called_once()
                attempt = llm.usage.attempts[0]
                self.assertEqual(attempt["outcome"], kind)
                self.assertEqual(attempt["request_timeout_seconds"], 17)
                self.assertIsNone(attempt["input_tokens"])
                self.assertNotIn("private", str(logs.output))
                self.assertNotIn("secret", str(error.exception))
        wait.assert_not_called()

    @patch("llm_provider.sleep")
    def test_503_retry_is_measured_and_only_once_per_analysis(self, wait):
        llm = self.llm()
        create = llm._deepseek_client.chat.completions.create
        create.side_effect = [self.error(503), response(), self.error(503)]
        self.assertEqual(llm.call("test"), "Complete")
        self.assertEqual(len(llm.usage.attempts), 2)
        self.assertEqual(llm.usage.logical_calls, 1)
        self.assertEqual(llm.usage.attempts[0]["status_code"], 503)
        llm.call("test again")
        self.assertEqual(create.call_count, 3)
        llm._groq_client.chat.completions.create.assert_called_once()
        wait.assert_called_once_with(2)

    @patch("llm_provider.sleep")
    def test_second_503_falls_back_and_other_errors_do_not_retry(self, wait):
        for status, expected in [(503, 2), (402, 1), (401, 1), (403, 1),
                                 (429, 1), (413, 1), (500, 1)]:
            with self.subTest(status=status):
                llm = self.llm()
                create = llm._deepseek_client.chat.completions.create
                create.side_effect = self.error(status)
                self.assertEqual(llm.call("test"), "Complete")
                self.assertEqual(create.call_count, expected)

    @patch("llm_provider.sleep")
    def test_retry_respects_budget_and_deadline(self, wait):
        llm = self.llm(max_attempts=1)
        llm._deepseek_client.chat.completions.create.side_effect = self.error(503)
        with self.assertRaises(InterpretationUnavailable):
            llm.call("test")
        wait.assert_not_called()
        self.assertEqual(len(llm.usage.attempts), 1)

        llm = self.llm()
        llm.providers = llm.providers[:1]
        llm.usage.deadline = 10
        llm._deepseek_client.chat.completions.create.side_effect = self.error(503)
        with patch("llm_provider.monotonic", return_value=9):
            with self.assertRaises(InterpretationUnavailable):
                llm.call("test")
        wait.assert_not_called()
        self.assertEqual(llm._deepseek_client.chat.completions.create.call_args.kwargs["timeout"], 1)

        llm = self.llm()
        llm.usage.deadline = 10
        llm._deepseek_client.chat.completions.create.side_effect = self.error(503)
        now = [0]
        wait.side_effect = lambda _: now.__setitem__(0, 11)
        with patch("llm_provider.monotonic", side_effect=lambda: now[0]):
            with self.assertRaises(InterpretationUnavailable):
                llm.call("test")
        self.assertEqual(len(llm.usage.attempts), 1)
        llm._groq_client.chat.completions.create.assert_not_called()

    @patch("llm_provider.sleep")
    def test_single_provider_second_503_remains_unavailable(self, wait):
        llm = self.llm()
        llm.providers = llm.providers[:1]
        llm._deepseek_client.chat.completions.create.side_effect = self.error(503)
        with self.assertRaises(InterpretationUnavailable) as error:
            llm.call("test")
        self.assertEqual(error.exception.code, "interpretation_unavailable")
        self.assertEqual(len(llm.usage.attempts), 2)
        self.assertEqual(llm.usage.logical_calls, 1)
        wait.assert_called_once_with(2)

    def llm(self, **limits):
        with patch("llm_provider.OpenAI"):
            llm = ConfigurableLLM(configured_providers({"DEEPSEEK_API_KEY": "test",
                "GROQ_API_KEY": "test"}), **limits)
        llm._deepseek_client = Mock()
        llm._groq_client = Mock()
        llm._deepseek_client.chat.completions.create.return_value = response()
        llm._groq_client.chat.completions.create.return_value = response()
        return llm

    def test_fallback_counts_attempts_not_just_logical_calls(self):
        with analysis_usage("PETR4.SA") as meter:
            llm = self.llm()
            exc = RuntimeError("secret response body")
            exc.status_code = 402
            llm._deepseek_client.chat.completions.create.side_effect = exc
            with self.assertLogs("llm_usage", level="INFO") as logs:
                llm.call("secret prompt")
                meter.stage = "quant"
                llm.call("secret prompt")
            self.assertNotIn("secret", str(logs.output))
            summary = meter.summary()
            self.assertEqual(summary["logical_calls"], 2)
            self.assertEqual(summary["attempts"], 3)
            self.assertEqual(summary["providers"][0]["usage_reported"], 0)
            self.assertEqual(summary["providers"][1]["input_tokens_reported"], 200)
            self.assertEqual(summary["providers"][1]["output_tokens_reported"], 40)
            self.assertEqual(meter.attempts[-1]["stage"], "quant")

    def test_budget_blocks_fallback_before_second_request(self):
        llm = self.llm(max_attempts=1)
        llm._deepseek_client.chat.completions.create.side_effect = RuntimeError("offline")
        with self.assertRaises(InterpretationUnavailable) as error:
            llm.call("test")
        self.assertEqual(error.exception.code, "interpretation_attempt_limit")
        llm._groq_client.chat.completions.create.assert_not_called()
        self.assertEqual(len(llm.usage.attempts), 1)

    def test_oversize_request_does_not_send_or_truncate(self):
        llm = self.llm(max_request_chars=20)
        with self.assertRaises(InterpretationUnavailable) as error:
            llm.call("x" * 100)
        self.assertEqual(error.exception.code, "interpretation_request_limit")
        llm._deepseek_client.chat.completions.create.assert_not_called()
        llm._groq_client.chat.completions.create.assert_not_called()
        self.assertEqual(llm.usage.summary()["attempts"], 0)

    def test_truncated_response_usage_is_preserved_and_missing_usage_is_null(self):
        llm = self.llm()
        llm._deepseek_client.chat.completions.create.return_value = response("length")
        llm._groq_client.chat.completions.create.return_value = response(usage=False)
        self.assertEqual(llm.call("test"), "Complete")
        self.assertEqual(llm.usage.attempts[0]["output_tokens"], 20)
        self.assertNotEqual(llm.usage.attempts[0]["outcome"], "success")
        self.assertIsNone(llm.usage.attempts[1]["output_tokens"])

    def test_concurrent_analyses_and_zero_call_summary(self):
        def run(index):
            token = job_id.set(str(index))
            try:
                with analysis_usage("VALE3.SA") as meter:
                    self.assertIs(meter, current_usage.get())
                    self.assertEqual(meter.summary()["attempts"], 0)
                    return meter.analysis_id
            finally:
                job_id.reset(token)
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(run, range(4)))
        self.assertEqual(ids, ["0", "1", "2", "3"])
        self.assertIsNone(current_usage.get())


if __name__ == "__main__":
    unittest.main()

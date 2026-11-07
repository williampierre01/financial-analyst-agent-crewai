"""Gemini wire contracts: real SDK serialization, simulated HTTP only."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

import httpx
from openai import OpenAI
from crewai.utilities.agent_utils import build_tool_calls_assistant_message

from llm_config import configured_providers
from llm_provider import ConfigurableLLM, InterpretationUnavailable


def completion(message=None, reason="stop", usage=True):
    body = {"id": "offline", "object": "chat.completion", "created": 0,
            "model": "gemini-test", "choices": [{"index": 0,
                "finish_reason": reason,
                "message": message or {"role": "assistant", "content": "Complete"}}]}
    if usage:
        body["usage"] = {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150}
    return body


def tool_turn(suffix="1"):
    return {"role": "assistant", "content": "Consultando a fonte.", "tool_calls": [
        {"id": "call-" + suffix, "type": "function",
         "function": {"name": "get_market_news", "arguments": '{"ticker":"PETR4"}'},
         "extra_content": {"google": {"thought_signature": "opaque-secret-" + suffix}}},
        {"id": "parallel-" + suffix, "type": "function",
         "function": {"name": "get_market_news", "arguments": '{"ticker":"VALE3"}'}}]}


class GeminiTests(unittest.TestCase):
    def make_llm(self, replies, fallback="none", **limits):
        self.requests = []

        def handle(request):
            self.requests.append((request.url.host, json.loads(request.content)))
            status, body = replies.pop(0)
            return httpx.Response(status, json=body)

        def client(**kwargs):
            result = OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handle)))
            self.addCleanup(result.close)
            return result

        env = {"LLM_PRIMARY_PROVIDER": "gemini", "LLM_FALLBACK_PROVIDER": fallback,
               "GEMINI_MODEL": "gemini-test", "GEMINI_API_KEY": "offline-key", "GROQ_API_KEY": "offline"}
        with patch("llm_provider.OpenAI", side_effect=client):
            return ConfigurableLLM(configured_providers(env), **limits)

    def test_explicit_model_key_and_selection(self):
        base = {"LLM_PRIMARY_PROVIDER": "gemini", "LLM_FALLBACK_PROVIDER": "none"}
        for addition in ({}, {"GEMINI_API_KEY": "key"}, {"GEMINI_MODEL": "gemini-test"}):
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                configured_providers({**base, **addition})
        config = configured_providers({**base, "GEMINI_API_KEY": "key", "GEMINI_MODEL": "gemini-test"})[0]
        self.assertEqual(config.base_url, "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.assertEqual(config.max_tokens, 8000)

    def test_tool_history_survives_crewai_rebuild_and_sdk_serialization(self):
        first, second = tool_turn("1"), tool_turn("2")
        llm = self.make_llm([(200, completion(first)), (200, completion(second)), (200, completion())])
        messages = [{"role": "user", "content": "Compare notícias"}]
        tools = [{"type": "function", "function": {"name": "get_market_news",
                  "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}}}}]
        with self.assertLogs("llm_usage", level="INFO") as logs:
            for _ in range(2):
                calls = llm.call(messages, tools=tools)
                assistant, reports = build_tool_calls_assistant_message(calls)
                self.assertNotIn("extra_content", reports[0])
                messages.append(assistant)
                messages.extend({"role": "tool", "tool_call_id": r["id"], "content": "Fonte recebida"}
                                for r in reports)
            original = deepcopy(messages)
            self.assertEqual(llm.call(messages, tools=tools), "Complete")
        self.assertEqual(messages, original)
        sent = self.requests[-1][1]
        self.assertEqual(sent["messages"][1], first)
        self.assertEqual(sent["messages"][4], second)
        self.assertEqual(sent["tools"], tools)
        self.assertEqual(sent["reasoning_effort"], "low")
        self.assertEqual(sent["max_tokens"], 8000)
        self.assertEqual(llm.usage.summary()["providers"][0]["input_tokens_reported"], 360)
        self.assertNotIn("opaque-secret", str(logs.output))
        self.assertNotIn("offline-key", str(logs.output))

    def test_rate_limit_fallback_does_not_leak_signatures(self):
        llm = self.make_llm([(200, completion(tool_turn())),
            (429, {"error": {"message": "private provider body"}}), (200, completion())], fallback="groq")
        calls = llm.call("News")
        assistant, _ = build_tool_calls_assistant_message(calls)
        self.assertEqual(llm.call([{"role": "user", "content": "News"}, assistant,
            {"role": "tool", "tool_call_id": calls[0].id, "content": "result"}]), "Complete")
        self.assertEqual(self.requests[-1][0], "api.groq.com")
        self.assertNotIn("extra_content", json.dumps(self.requests[-1][1]))
        self.assertNotIn("reasoning_effort", self.requests[-1][1])
        self.assertEqual([a["outcome"] for a in llm.usage.attempts], ["success", "rate_limit", "success"])

    def test_foreign_tool_history_not_sent_to_gemini(self):
        llm = self.make_llm([])
        with self.assertRaises(InterpretationUnavailable):
            llm.call([tool_turn()])
        self.assertEqual(self.requests, [])

    def test_signature_state_is_not_shared_between_analyses(self):
        llm = self.make_llm([(200, completion(tool_turn()))])
        calls = llm.call("News")
        assistant, _ = build_tool_calls_assistant_message(calls)
        other = self.make_llm([])
        with self.assertRaises(InterpretationUnavailable):
            other.call([assistant])
        self.assertEqual(self.requests, [])

    def test_restored_signatures_cannot_bypass_character_limit(self):
        turn = tool_turn()
        turn["tool_calls"][0]["extra_content"]["google"]["thought_signature"] = "x" * 5000
        llm = self.make_llm([(200, completion(turn))], max_request_chars=2000)
        calls = llm.call("News")
        assistant, _ = build_tool_calls_assistant_message(calls)
        with self.assertRaises(InterpretationUnavailable):
            llm.call([assistant])
        self.assertEqual(len(self.requests), 1)

    def test_truncated_and_missing_usage_remain_explicit(self):
        llm = self.make_llm([(200, completion(reason="length"))])
        with self.assertRaises(InterpretationUnavailable):
            llm.call("News")
        self.assertEqual(llm.usage.attempts[0]["output_tokens"], 30)
        llm = self.make_llm([(200, completion(usage=False))])
        self.assertEqual(llm.call("News"), "Complete")
        self.assertIsNone(llm.usage.attempts[0]["input_tokens"])


if __name__ == "__main__":
    unittest.main()

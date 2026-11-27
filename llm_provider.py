"""Configurable providers; CrewAI owns native tool execution."""
from __future__ import annotations

import logging
import json
import os
from copy import deepcopy
from time import monotonic, sleep
from llm_config import ProviderConfig, bounded_int, configured_providers
from llm_usage import UsageMeter, current_usage
from typing import Any, Dict, List, Optional, Union

from crewai import BaseLLM
from openai import OpenAI, APITimeoutError, APIConnectionError

logger = logging.getLogger("llm_provider")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"  # thinking mode ligado via extra_body

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"

# Output caps chosen by this application, not provider quotas or free credits.
# Account rate limits and remaining balance are independent of these caps.
DEEPSEEK_MAX_TOKENS = 8000
GROQ_MAX_TOKENS = 2500

# campos que o schema de chat completions OpenAI-compatible realmente aceita.
# O CrewAI injeta campos proprios (ex: cache_breakpoint, usado como dica de
# cache de contexto pra providers nativos) que a API da DeepSeek rejeita com
# 400 se forem repassados sem filtro.
_ALLOWED_MESSAGE_KEYS = {"role", "content", "name", "tool_calls", "tool_call_id"}


class InterpretationUnavailable(RuntimeError):
    """Only fixed, public messages may cross the agent/UI boundary."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.public_message = message
        super().__init__(message)


def provider_failure(exc: Exception) -> str:
    # Typed SDK errors only: never infer a timeout from elapsed time or body text.
    if isinstance(exc, (APITimeoutError, TimeoutError)):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "connection"
    return {402: "balance", 413: "capacity", 429: "rate_limit",
            401: "credentials", 403: "credentials"}.get(
                getattr(exc, "status_code", None), "unavailable")


def public_failure(exc: Exception) -> dict[str, str] | None:
    """Inspect typed causes, never parse or return provider response bodies."""
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if isinstance(exc, InterpretationUnavailable):
            return {"code": exc.code, "message": exc.public_message}
        exc = exc.__cause__ or exc.__context__
    return None


def _sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized = []
    for m in messages:
        if isinstance(m, dict):
            sanitized.append({k: v for k, v in m.items() if k in _ALLOWED_MESSAGE_KEYS})
        else:
            sanitized.append(m)
    return sanitized


class ConfigurableLLM(BaseLLM):
    """One instance per analysis, one SDK request per measured attempt."""

    def __init__(self, providers, temperature=0.3, *, max_attempts=12,
                 max_request_chars=60000, timeout=60):
        if not providers:
            raise ValueError("Nenhum provedor configurado")
        super().__init__(model=providers[0].model, temperature=temperature)
        self.providers = providers
        self.max_attempts = max_attempts
        self.max_request_chars = max_request_chars
        self.request_timeout = timeout
        self._retried_503 = False
        self.usage = current_usage.get() or UsageMeter()
        self._disabled = set()
        # CrewAI rebuilds tool messages without Google's opaque signatures.
        # Keep original assistant turns only in this analysis, never in logs.
        self._gemini_tool_turns = {}
        self.last_provider_used = None
        for provider in providers:
            setattr(self, "_" + provider.name + "_client", OpenAI(
                api_key=provider.api_key, base_url=provider.base_url,
                max_retries=0, timeout=timeout))

    def supports_function_calling(self) -> bool:
        return True

    @staticmethod
    def _tool_turn_key(calls):
        return json.dumps([{k: c.get(k) for k in ("id", "type", "function")}
                           for c in calls], sort_keys=True, ensure_ascii=False)

    def _provider_messages(self, messages, provider_name, model):
        result = deepcopy(messages)
        for index, message in enumerate(result):
            calls = message.get("tool_calls")
            if not calls:
                continue
            if provider_name == "gemini":
                saved = self._gemini_tool_turns.get((model, self._tool_turn_key(calls)))
                if saved is None:
                    # Never invent signatures or replay another provider's turn
                    # as if Gemini had generated it. Fallback can try next provider.
                    raise RuntimeError("Histórico de ferramentas incompatível com Gemini")
                result[index] = deepcopy(saved)
            else:
                for call in calls:
                    call.pop("extra_content", None)
        return result

    # ------------------------------------------------------------------ #
    # Interface exigida pelo BaseLLM do CrewAI
    # ------------------------------------------------------------------ #

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,  # absorve extras que versoes do CrewAI possam passar
                        # (ex: from_task, from_agent) sem quebrar a chamada
    ) -> Union[str, Any]:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        else:
            messages = list(messages)
        messages = _sanitize_messages(messages)

        self.usage.logical_calls += 1
        # Local character bound, NOT a token estimate or TPM guarantee.
        size = len(json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False))
        if size > self.max_request_chars:
            raise InterpretationUnavailable("interpretation_request_limit",
                "O texto excedeu o limite configurado de IA. Os dados financeiros continuam disponíveis.")
        kind = "unavailable"
        for provider in self.providers:
            if provider.name in self._disabled:
                continue
            if len(self.usage.attempts) >= self.max_attempts:
                raise InterpretationUnavailable("interpretation_attempt_limit",
                    "A análise atingiu o limite de chamadas de IA. Os dados financeiros continuam disponíveis.")
            try:
                return self._call_with_retry(
                    client=getattr(self, "_" + provider.name + "_client"),
                    model=provider.model, provider_name=provider.name,
                    messages=messages, tools=tools, extra_body=provider.extra_body,
                    max_tokens=provider.max_tokens)
            except Exception as exc:
                kind = provider_failure(exc)
                if kind in {"balance", "credentials"}:
                    self._disabled.add(provider.name)
                logger.warning("llm_fallback provider=%s kind=%s", provider.name, kind)
        message = {
            "timeout": "O serviço de IA não respondeu dentro do prazo da chamada.",
            "connection": "Não foi possível estabelecer ou manter a conexão com o serviço de IA.",
            "capacity": "O serviço de IA recusou o volume de texto desta análise.",
            "rate_limit": "O serviço de IA atingiu seu limite temporário de uso.",
            "balance": "O serviço de IA está sem saldo disponível.",
            "credentials": "O serviço de IA está com um problema de credenciais ou permissão.",
            "unavailable": "A resposta do serviço de IA ficou indisponível ou foi interrompida.",
        }[kind]
        if any(a["provider"] == "deepseek" and a["outcome"] == "balance" for a in self.usage.attempts):
            message = "O DeepSeek está sem saldo. " + message
        raise InterpretationUnavailable("interpretation_" + kind,
            message + " Os dados financeiros continuam disponíveis.") from None

    # ------------------------------------------------------------------ #
    # Uma unica chamada de API. Nao executa tools nem faz loop -- isso e
    # responsabilidade do executor nativo do CrewAI.
    # ------------------------------------------------------------------ #

    def _remaining(self):
        if self.usage.deadline is None:
            return self.request_timeout
        return self.usage.deadline - monotonic()

    def _call_with_retry(self, **kwargs):
        for retry in range(2):
            remaining = self._remaining()
            if remaining <= 0:
                raise RuntimeError("Prazo da análise encerrado")
            try:
                return self._call_once(timeout=min(self.request_timeout, remaining), **kwargs)
            except Exception as exc:
                if (retry or self._retried_503 or getattr(exc, "status_code", None) != 503
                        or len(self.usage.attempts) >= self.max_attempts
                        or self._remaining() <= 2):
                    raise
                self._retried_503 = True
                logger.warning("llm_retry analysis_id=%s provider=%s status=503 delay_seconds=2",
                               self.usage.analysis_id, kwargs["provider_name"])
                sleep(2)

    def _call_once(self, **kwargs):
        started = monotonic()
        attempt = dict(provider=kwargs["provider_name"], model=kwargs["model"],
                       stage=self.usage.stage, logical_call=self.usage.logical_calls,
                       outcome="unavailable", input_tokens=None, output_tokens=None,
                       request_timeout_seconds=kwargs["timeout"])
        try:
            result = self._complete(attempt=attempt, **kwargs)
            attempt["outcome"] = "success"
            return result
        except Exception as exc:
            attempt["outcome"] = provider_failure(exc)
            status = getattr(exc, "status_code", None)
            if type(status) is int:
                attempt["status_code"] = status
            raise
        finally:
            attempt["duration_ms"] = round((monotonic() - started) * 1000)
            self.usage.record(attempt)

    def _complete(
        self,
        client: OpenAI,
        model: str,
        provider_name: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[dict]],
        extra_body: Optional[dict],
        max_tokens: int,
        attempt: dict,
        timeout: float,
    ) -> Union[str, List[Any]]:
        self.last_provider_used = provider_name

        messages = self._provider_messages(messages, provider_name, model)
        # Signatures are part of the transmitted body and must fit the same cap.
        if len(json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False)) > self.max_request_chars:
            raise RuntimeError("Histórico do provedor excede o limite configurado")

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "timeout": timeout,
        }
        if tools:
            kwargs["tools"] = tools
        if extra_body:
            kwargs["extra_body"] = extra_body

        response = client.chat.completions.create(**kwargs)
        usage = getattr(response, "usage", None)
        for source, target in [("prompt_tokens", "input_tokens"), ("completion_tokens", "output_tokens")]:
            value = getattr(usage, source, None)
            if type(value) is int and value >= 0:
                attempt[target] = value
        # A nonempty fragment is still incomplete when the provider reports a cut.
        if getattr(response.choices[0], "finish_reason", None) in {"length", "content_filter"}:
            raise RuntimeError("Resposta do provedor interrompida antes da conclusão")
        message = response.choices[0].message

        # o reasoning_content (quando existe) fica de fora do texto que
        # segue pro parser de tools -- so logamos, nunca reinjetamos no
        # content que o CrewAI vai tentar interpretar.
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning:
            logger.info(
                "[%s] reasoning_content (%d chars) descartado do fluxo de tool-calling",
                provider_name,
                len(reasoning),
            )

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            if provider_name == "gemini":
                saved = message.model_dump(exclude_none=True)
                saved = {k: v for k, v in saved.items()
                         if k in _ALLOWED_MESSAGE_KEYS or k == "extra_content"}
                key = (model, self._tool_turn_key(saved["tool_calls"]))
                self._gemini_tool_turns[key] = deepcopy(saved)
            # devolve a lista crua (objetos com .function.name/.function.arguments)
            # -- o executor nativo do CrewAI reconhece esse formato e executa
            # as tools e o loop por conta propria.
            return list(tool_calls)

        content = message.content or ""
        if not content.strip():
            finish_reason = getattr(response.choices[0], "finish_reason", "desconhecido")
            raise RuntimeError(
                f"[{provider_name}] resposta vazia (finish_reason={finish_reason}) "
                "-- provavelmente o orcamento de tokens acabou durante o "
                "raciocinio antes de gerar o conteudo final"
            )
        return content


class DeepSeekGroqFallbackLLM(ConfigurableLLM):
    """Compatibility constructor; application code uses get_llm."""

    def __init__(self, deepseek_api_key, groq_api_key, temperature=0.3):
        super().__init__([
            ProviderConfig("deepseek", DEEPSEEK_MODEL, deepseek_api_key,
                           DEEPSEEK_BASE_URL, DEEPSEEK_MAX_TOKENS,
                           {"thinking": {"type": "enabled"}}),
            ProviderConfig("groq", GROQ_MODEL, groq_api_key, GROQ_BASE_URL, GROQ_MAX_TOKENS),
        ], temperature=temperature)


def get_llm(deepseek_api_key=None, groq_api_key=None):
    env = dict(os.environ)
    if deepseek_api_key is not None:
        env["DEEPSEEK_API_KEY"] = deepseek_api_key
    if groq_api_key is not None:
        env["GROQ_API_KEY"] = groq_api_key
    try:
        providers = configured_providers(env)
        return ConfigurableLLM(providers,
            max_attempts=bounded_int(env, "LLM_MAX_ATTEMPTS", 12, 30),
            max_request_chars=bounded_int(env, "LLM_MAX_REQUEST_CHARS", 60000, 200000),
            timeout=bounded_int(env, "LLM_TIMEOUT_SECONDS", 60, 120))
    except ValueError:
        raise InterpretationUnavailable("interpretation_configuration",
            "A configuração dos serviços de IA precisa ser revisada. Os dados financeiros continuam disponíveis.") from None

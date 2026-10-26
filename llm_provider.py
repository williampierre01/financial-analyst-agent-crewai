"""
Camada de LLM com fallback de provedor: DeepSeek V4 Flash (thinking mode) como
primario, Groq gpt-oss-120b como fallback automatico.

Por que uma classe BaseLLM customizada em vez do wrapper padrao do CrewAI
(litellm)? Duas razoes tecnicas:

1. Ha um bug conhecido no litellm (issue #27439, maio/2026) que descarta o
   parametro reasoning_effort especificamente na integracao com DeepSeek V4,
   substituindo sempre por thinking:enabled sem controle fino.
2. O modo thinking do V4 retorna o raciocinio em `reasoning_content`,
   separado do `content` final -- controlando isso manualmente, garantimos
   que o reasoning trace NUNCA vaza pro parser de tool-calling do agente
   (o problema classico do <think> tag que quebrava o R1 antigo).

Nota de arquitetura (importante): a primeira versao deste arquivo implementava
um loop manual de tool-calling (chamando as funcoes e reinjetando o resultado).
Isso estava errado para essa versao do CrewAI (1.15.x): o modulo
`crewai.experimental.agent_executor` tem seu PROPRIO executor nativo de tool
calling (`call_llm_native_tools`), que chama nosso `call()` sempre com
`available_functions=None` de proposito -- ele espera que devolvamos a LISTA
BRUTA de tool_calls (formato OpenAI: objetos com atributo `.function`) quando
o modelo pedir uma ferramenta, e o proprio CrewAI executa a chamada e faz o
loop, nao nos. Confirmado lendo o codigo-fonte instalado
(crewai/utilities/agent_utils.py::is_tool_call_list).

Ambos os provedores sao OpenAI-compatible, entao usamos um unico cliente
`openai.OpenAI` trocando so o base_url e a chave.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from crewai import BaseLLM
from openai import OpenAI

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


class DeepSeekGroqFallbackLLM(BaseLLM):
    """LLM customizado com fallback DeepSeek -> Groq.

    Tenta o primario e, se necessario, o fallback. Quando o modelo decide
    chamar uma ferramenta, devolvemos a lista de tool_calls crua -- quem
    executa e faz o loop de tool-calling e o proprio executor nativo do
    CrewAI, nao esta classe.
    """

    def __init__(
        self,
        deepseek_api_key: str,
        groq_api_key: str,
        temperature: Optional[float] = 0.3,
    ):
        # BaseLLM exige o atributo `model` -- usamos o nome do primario aqui,
        # o real provider ativo e decidido em runtime no fallback.
        super().__init__(model=DEEPSEEK_MODEL, temperature=temperature)
        self._deepseek_client = OpenAI(api_key=deepseek_api_key, base_url=DEEPSEEK_BASE_URL)
        self._groq_client = OpenAI(api_key=groq_api_key, base_url=GROQ_BASE_URL)
        self.last_provider_used: Optional[str] = None
        # One instance is shared by this analysis only; a new analysis retries billing.
        self._deepseek_without_balance = False

    def supports_function_calling(self) -> bool:
        return True

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

        if not self._deepseek_without_balance:
            try:
                return self._call_once(
                    client=self._deepseek_client,
                    model=DEEPSEEK_MODEL,
                    provider_name="deepseek",
                    messages=messages,
                    tools=tools,
                    extra_body={"thinking": {"type": "enabled"}},
                    max_tokens=DEEPSEEK_MAX_TOKENS,
                )
            except Exception as exc:  # noqa: BLE001
                kind = provider_failure(exc)
                self._deepseek_without_balance = kind == "balance"
                logger.warning("llm_fallback provider=deepseek kind=%s", kind)
        try:
            return self._call_once(
                client=self._groq_client,
                model=GROQ_MODEL,
                provider_name="groq",
                messages=messages,
                tools=tools,
                extra_body=None,
                max_tokens=GROQ_MAX_TOKENS,
            )
        except Exception as exc:
            kind = provider_failure(exc)
            logger.warning("llm_unavailable provider=groq kind=%s deepseek_balance=%s",
                           kind, "empty" if self._deepseek_without_balance else "unknown")
            messages_by_kind = {
                "capacity": "O serviço alternativo de IA recusou o volume de texto desta análise.",
                "rate_limit": "O serviço alternativo de IA atingiu seu limite temporário de uso.",
                "balance": "O serviço alternativo de IA está sem saldo disponível.",
                "credentials": "O serviço alternativo de IA está com um problema de credenciais ou permissão.",
                "unavailable": "A resposta do serviço alternativo de IA ficou indisponível ou foi interrompida.",
            }
            message = messages_by_kind[kind]
            if self._deepseek_without_balance:
                message = "O DeepSeek está sem saldo. " + message
            message += " Os dados financeiros continuam disponíveis."
            # Suppress the original API body in tracebacks printed by CrewAI.
            raise InterpretationUnavailable("interpretation_" + kind, message) from None

    # ------------------------------------------------------------------ #
    # Uma unica chamada de API. Nao executa tools nem faz loop -- isso e
    # responsabilidade do executor nativo do CrewAI.
    # ------------------------------------------------------------------ #

    def _call_once(
        self,
        client: OpenAI,
        model: str,
        provider_name: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[dict]],
        extra_body: Optional[dict],
        max_tokens: int,
    ) -> Union[str, List[Any]]:
        self.last_provider_used = provider_name

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if extra_body:
            kwargs["extra_body"] = extra_body

        response = client.chat.completions.create(**kwargs)
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


def get_llm(deepseek_api_key: str, groq_api_key: str) -> DeepSeekGroqFallbackLLM:
    """Factory simples -- mantem agents.py desacoplado dos detalhes de provider."""
    return DeepSeekGroqFallbackLLM(
        deepseek_api_key=deepseek_api_key,
        groq_api_key=groq_api_key,
    )

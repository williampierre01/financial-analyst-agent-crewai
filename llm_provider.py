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

Ambos os provedores sao OpenAI-compatible, entao usamos um unico cliente
`openai.OpenAI` trocando so o base_url e a chave.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Union

from crewai import BaseLLM
from openai import OpenAI

logger = logging.getLogger("llm_provider")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"  # thinking mode ligado via extra_body

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"  # fallback gratuito permanente, tambem reasoning

MAX_TOOL_ROUNDS = 8  # trava de seguranca contra loop infinito de tool calling

# orcamento de tokens de saida por provider. O free tier do Groq tem um teto
# de TPM (tokens por minuto) BEM apertado -- 8000 tokens TOTAIS (prompt +
# resposta) por chamada nessa conta. Pedir max_tokens=8000 de saida sozinho
# ja estoura isso assim que o system prompt/tools do CrewAI entram na conta.
# A DeepSeek, com os 5M tokens de credito gratuito, aguenta um teto bem maior.
DEEPSEEK_MAX_TOKENS = 8000
GROQ_MAX_TOKENS = 1500

# campos que o schema de chat completions OpenAI-compatible realmente aceita.
# O CrewAI injeta campos proprios (ex: cache_breakpoint, usado como dica de
# cache de contexto pra providers nativos) que a API da DeepSeek rejeita com
# 400 se forem repassados sem filtro.
_ALLOWED_MESSAGE_KEYS = {"role", "content", "name", "tool_calls", "tool_call_id"}


def _sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized = []
    for m in messages:
        if isinstance(m, dict):
            sanitized.append({k: v for k, v in m.items() if k in _ALLOWED_MESSAGE_KEYS})
        else:
            sanitized.append(m)
    return sanitized


class DeepSeekGroqFallbackLLM(BaseLLM):
    """LLM customizado com fallback DeepSeek -> Groq e tool-calling loop manual."""

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
            messages = list(messages)  # copia -- vamos mutar essa lista
        messages = _sanitize_messages(messages)

        try:
            return self._run_tool_loop(
                client=self._deepseek_client,
                model=DEEPSEEK_MODEL,
                provider_name="deepseek",
                messages=messages,
                tools=tools,
                available_functions=available_functions,
                extra_body={"thinking": {"type": "enabled"}},
                max_tokens=DEEPSEEK_MAX_TOKENS,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "DeepSeek falhou (%s) -- caindo para Groq gpt-oss-120b", exc
            )
            return self._run_tool_loop(
                client=self._groq_client,
                model=GROQ_MODEL,
                provider_name="groq",
                messages=messages,
                tools=tools,
                available_functions=available_functions,
                extra_body=None,
                max_tokens=GROQ_MAX_TOKENS,
            )

    # ------------------------------------------------------------------ #
    # Loop de tool calling (mantido explicito para controlar o
    # reasoning_content e nao deixar o rastro de pensamento vazar pro
    # parser de ferramentas do agente)
    # ------------------------------------------------------------------ #

    def _final_answer(self, content: Optional[str], response: Any, provider_name: str) -> str:
        """Centraliza a checagem de resposta vazia -- usado em todo ponto de
        retorno do loop, para nunca devolver "" silenciosamente ao CrewAI."""
        content = content or ""
        if not content.strip():
            finish_reason = getattr(response.choices[0], "finish_reason", "desconhecido")
            raise RuntimeError(
                f"[{provider_name}] resposta vazia (finish_reason={finish_reason}) "
                "-- provavelmente o orcamento de tokens acabou durante o "
                "raciocinio antes de gerar o conteudo final"
            )
        return content

    def _run_tool_loop(
        self,
        client: OpenAI,
        model: str,
        provider_name: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[dict]],
        available_functions: Optional[Dict[str, Any]],
        extra_body: Optional[dict],
        max_tokens: int,
    ) -> str:
        self.last_provider_used = provider_name

        for round_num in range(MAX_TOOL_ROUNDS):
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
            message = response.choices[0].message

            # o reasoning_content (quando existe) fica de fora do texto que
            # segue pro parser de tools -- so logamos, nunca reinjetamos no
            # content que o CrewAI vai tentar interpretar como JSON de tool.
            reasoning = getattr(message, "reasoning_content", None)
            if reasoning:
                logger.info(
                    "[%s] reasoning_content (%d chars) descartado do fluxo de tool-calling",
                    provider_name,
                    len(reasoning),
                )

            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls:
                return self._final_answer(message.content, response, provider_name)

            if not available_functions:
                # o modelo pediu pra chamar uma tool mas nao recebemos
                # implementacoes -- mesma validacao de vazio se aplica aqui.
                return self._final_answer(message.content, response, provider_name)

            # registra a resposta do assistente (com tool_calls) no historico
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    fn_args = {}

                fn = available_functions.get(fn_name)
                if fn is None:
                    tool_result = f"erro: tool '{fn_name}' nao encontrada"
                else:
                    try:
                        tool_result = fn(**fn_args)
                    except Exception as exc:  # noqa: BLE001
                        tool_result = f"erro executando '{fn_name}': {exc}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                    }
                )

        # estourou o limite de rounds -- devolve o que tiver, nao trava o crew
        logger.error("MAX_TOOL_ROUNDS (%d) atingido para provider=%s", MAX_TOOL_ROUNDS, provider_name)
        return "Erro: numero maximo de chamadas de ferramenta excedido antes de uma resposta final."


def get_llm(deepseek_api_key: str, groq_api_key: str) -> DeepSeekGroqFallbackLLM:
    """Factory simples -- mantem agents.py desacoplado dos detalhes de provider."""
    return DeepSeekGroqFallbackLLM(
        deepseek_api_key=deepseek_api_key,
        groq_api_key=groq_api_key,
    )
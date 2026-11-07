"""Explicit provider allowlist and bounded server configuration."""
from dataclasses import dataclass, field
import os
import re


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key: str = field(repr=False)
    base_url: str
    max_tokens: int
    extra_body: dict | None = None


def bounded_int(env, name, default, maximum):
    try:
        value = int(env.get(name, str(default)))
    except (TypeError, ValueError):
        raise ValueError(f"Configuração inválida: {name}") from None
    if not 1 <= value <= maximum:
        raise ValueError(f"Configuração fora do limite: {name}")
    return value


def configured_providers(env=None):
    env = os.environ if env is None else env
    names = [env.get("LLM_PRIMARY_PROVIDER", "deepseek").strip().lower()]
    fallback = env.get("LLM_FALLBACK_PROVIDER", "groq").strip().lower()
    if fallback not in ("", "none"):
        names.append(fallback)
    if len(set(names)) != len(names) or any(n not in ("deepseek", "groq") for n in names):
        raise ValueError("Provedores de IA inválidos ou repetidos")
    defaults = {
        "deepseek": ("deepseek-v4-flash", "https://api.deepseek.com", 8000,
                     {"thinking": {"type": "enabled"}}),
        "groq": ("openai/gpt-oss-120b", "https://api.groq.com/openai/v1", 2500, None),
    }
    result = []
    for name in names:
        default_model, url, cap, extra = defaults[name]
        prefix = name.upper()
        model = env.get(prefix + "_MODEL", default_model).strip()
        # No arbitrary URLs, control characters or unbounded identifiers in logs.
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model):
            raise ValueError("Identificador de modelo inválido")
        key = env.get(prefix + "_API_KEY", "").strip()
        if not key:
            raise ValueError(f"Credencial ausente: {prefix}_API_KEY")
        result.append(ProviderConfig(name, model, key, url,
            bounded_int(env, prefix + "_MAX_OUTPUT_TOKENS", cap, 16000), extra))
    return result

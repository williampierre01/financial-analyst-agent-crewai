---
title: Financial Analyst Agent
emoji: 📈
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Financial Analyst Crew

Sistema multi-agente de análise financeira autônoma, usando CrewAI, um LLM de
raciocínio (DeepSeek V4 Flash em modo thinking, com fallback automático para
Groq gpt-oss-120b) e integração de ferramentas via Model Context Protocol
(MCP).

Projeto de portfólio — foco em zero custo de hospedagem/inferência e em
resiliência de arquitetura (não em precisão financeira real; ver disclaimers
gerados pelo próprio relatório).

🔗 **App no ar:** [huggingface.co/spaces/willp01/financial-analyst-crew-mcp](https://huggingface.co/spaces/willp01/financial-analyst-crew-mcp)

## Status

- [x] **Etapa 1** — Servidor MCP com tools de dados financeiros
- [x] **Etapa 2** — Camada de fallback de LLM + agentes CrewAI
- [x] **Etapa 3** — Interface Gradio + deploy no Hugging Face Spaces

## Arquitetura

```
Gradio UI (app.py)
      │  (thread separada + fila, para streaming de progresso)
      ▼
CrewAI Crew (agents.py) — Process.sequential
  Data Gatherer → Quant Analyst → CIO
      │
      ├── MCPServerAdapter ──► mcp_server.py (subprocesso stdio)
      │                          ├── get_financial_statements (yfinance→Stooq)
      │                          └── get_market_news (ddgs)
      │
      └── DeepSeekGroqFallbackLLM (llm_provider.py)
                 DeepSeek V4 Flash (thinking) ──falha──► Groq gpt-oss-120b
```

## Etapa 1 — Servidor MCP (`mcp_server.py`)

Duas tools, ambas com saída validada por Pydantic:

- **`get_financial_statements(ticker)`**: DRE, Balanço, Fluxo de Caixa e
  cotação atual. Fundamentos vêm exclusivamente do `yfinance` — não há
  fallback gratuito equivalente para demonstrativos financeiros. A cotação,
  por sua vez, tem fallback no Stooq caso o yfinance falhe. O payload é
  reduzido de propósito (2 períodos mais recentes, só as linhas essenciais
  de cada demonstrativo) para não estourar o orçamento de contexto dos
  provedores de LLM gratuitos mais adiante no pipeline.
- **`get_market_news(ticker)`**: notícias recentes via `ddgs` (o pacote
  antigo `duckduckgo-search` foi renomeado e está deprecado).

Toda chamada externa instável (yfinance) usa retry com backoff exponencial
(`tenacity`). Falhas nunca retornam dado malformado silenciosamente — o
schema expõe `fundamentals_available: bool` e um campo `warning` explícito.

```bash
python test_tools.py AAPL
python test_tools.py PETR4.SA
python test_tools.py TICKER_INVALIDO_XPTO   # valida o caminho de fallback
```

## Etapa 2 — LLM com fallback + agentes (`llm_provider.py`, `agents.py`)

- **`DeepSeekGroqFallbackLLM`**: subclasse de `BaseLLM` do CrewAI. Tenta
  DeepSeek V4 Flash (modo thinking) primeiro; qualquer exceção (saldo
  insuficiente, timeout, resposta vazia) aciona fallback automático para
  Groq gpt-oss-120b. Sanitiza mensagens antes de enviar (remove campos
  internos do CrewAI, como `cache_breakpoint`, que quebram a validação
  estrita de schema da API da DeepSeek) e mantém orçamentos de tokens
  diferentes por provedor (o free tier do Groq tem um teto de 8.000
  tokens/min por chamada — bem mais apertado que o da DeepSeek).
- **Tool calling nativo**: o CrewAI 1.15.x tem seu próprio executor de tool
  calling (`call_llm_native_tools`) — o `call()` customizado só precisa
  devolver a lista bruta de `tool_calls` quando o modelo pedir uma
  ferramenta; quem executa e faz o loop é o próprio CrewAI, não esta classe.
- **Agentes**: Data Gatherer → Quant Analyst → CIO, topologia sequencial,
  consumindo o servidor MCP via `MCPServerAdapter` (mais estável, nesta
  versão do CrewAI, que o campo nativo `mcps`).

```bash
python agents.py AAPL
```

## Etapa 3 — Interface Gradio (`app.py`)

`crew.kickoff()` é bloqueante, então a execução roda numa thread separada;
os callbacks de mudança de estágio de cada `Task` empurram atualizações por
uma fila thread-safe que o generator do Gradio consome via `yield`,
mostrando progresso simples ("Data Gatherer coletando..." → "Quant Analyst
calculando..." → "CIO sintetizando...") em vez de travar a tela por 1-2
minutos.

```bash
python app.py
```

### Deploy

O Space é sincronizado automaticamente do GitHub via GitHub Actions
(`.github/workflows/sync-to-hf-space.yml`, usando a action oficial
`huggingface/hub-sync`). Todo push na branch `main` atualiza o Space.
As chaves `DEEPSEEK_API_KEY` e `GROQ_API_KEY` são configuradas como secrets
diretamente nas Settings do Space (não no GitHub).

## Lições de engenharia (por que várias decisões foram tomadas)

- **DeepSeek-R1 → DeepSeek V4 Flash**: o modelo `deepseek-reasoner` (R1)
  foi descontinuado pela DeepSeek pouco depois do início do projeto;
  migramos para `deepseek-v4-flash` em modo thinking.
- **Nunca confiar em "sucesso sem exceção" como sucesso de verdade**: a
  API pode retornar 200 com conteúdo vazio (orçamento de tokens esgotado
  em raciocínio antes da resposta final). O `llm_provider.py` valida
  explicitamente conteúdo vazio e trata como falha, disparando o fallback.
- **Payload de tool enxuto**: reduzir o que a tool devolve (períodos e
  linhas) importa tanto quanto reduzir o `max_tokens` de saída — o
  histórico de conversa cresce com cada resultado de tool, e isso conta
  contra o mesmo orçamento de contexto.
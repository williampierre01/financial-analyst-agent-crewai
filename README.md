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

Projeto de portfólio — foco em resiliência de arquitetura (fallback de LLM
e de provedor de dados) e não em precisão financeira real (ver disclaimers
gerados pelo próprio relatório).

🔗 **App no ar (Render):** [financial-analyst-agent-crewai.onrender.com](https://financial-analyst-agent-crewai.onrender.com)
*(free tier — a primeira requisição após inatividade pode levar 30-60s pra "acordar")*

📦 **Space na Hugging Face:** pausado por decisão consciente — hospedar
Gradio/Docker em CPU básica passou a exigir assinatura PRO na HF (mudança de
política, julho/2026). Reativar quando o upgrade for feito; nenhum código
precisa mudar para isso.

## Status — v1 encerrada

- [x] **Etapa 1** — Servidor MCP com tools de dados financeiros (yfinance + FMP)
- [x] **Etapa 2** — Camada de fallback de LLM + agentes CrewAI
- [x] **Etapa 3** — Interface Gradio + deploy (Render)
- [x] **Etapa extra** — Fallback de provedor de dados (FMP), resolvendo bloqueio de IP de datacenter do yfinance em nuvem

Próximas versões (v2+: modo comparação entre providers, escolha de LLM pelo
usuário, versão "light" vs "completa") ficam para uma iteração futura deste
projeto, não fazem parte desta v1.

## Arquitetura

```
Gradio UI (app.py)
      │  (thread separada + fila, para streaming de progresso)
      │  dropdown: fonte de dados (yfinance | FMP)
      ▼
CrewAI Crew (agents.py) — Process.sequential
  Data Gatherer → Quant Analyst → CIO
      │
      ├── MCPServerAdapter ──► mcp_server.py (subprocesso stdio)
      │                          ├── get_financial_statements(ticker, provider)
      │                          │      "yfinance" (padrao) ──falha──► Stooq (so cotacao)
      │                          │      "fmp" (API autenticada, sem bloqueio de IP)
      │                          └── get_market_news (ddgs)
      │
      └── DeepSeekGroqFallbackLLM (llm_provider.py)
                 DeepSeek V4 Flash (thinking) ──falha──► Groq gpt-oss-120b
```

## Etapa 1 — Servidor MCP (`mcp_server.py`)

Duas tools, ambas com saída validada por Pydantic:

- **`get_financial_statements(ticker, provider)`**: DRE, Balanço, Fluxo de
  Caixa e cotação atual. Dois providers:
  - `"yfinance"` (padrão): gratuito, mas a Yahoo Finance bloqueia/limita IPs
    de datacenter — problema conhecido e documentado que afeta qualquer app
    rodando em nuvem (Render, Streamlit Cloud, etc.), não é bug deste
    projeto. Cotação tem fallback no Stooq quando esse provider falha.
  - `"fmp"` (Financial Modeling Prep): API oficial autenticada, 250
    requisições/dia grátis, não sofre bloqueio de IP por não ser scraping.
    Fallback real quando o yfinance falha em ambiente de nuvem.
  O payload é reduzido de propósito (2 períodos mais recentes, só as linhas
  essenciais de cada demonstrativo) para não estourar o orçamento de
  contexto dos provedores de LLM gratuitos mais adiante no pipeline.
- **`get_market_news(ticker)`**: notícias recentes via `ddgs` (o pacote
  antigo `duckduckgo-search` foi renomeado e está deprecado).

Toda chamada externa instável usa retry com backoff exponencial (`tenacity`).
Falhas nunca retornam dado malformado silenciosamente — o schema expõe
`fundamentals_available: bool`, `provider_used: str` e um campo `warning`
explícito.

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
  versão do CrewAI, que o campo nativo `mcps`). `data_provider` é propagado
  do dropdown da UI até a instrução do Data Gatherer.

```bash
python agents.py AAPL          # yfinance (padrao)
python agents.py AAPL fmp      # forca o provider FMP
```

## Etapa 3 — Interface Gradio (`app.py`)

`crew.kickoff()` é bloqueante, então a execução roda numa thread separada;
os callbacks de mudança de estágio de cada `Task` empurram atualizações por
uma fila thread-safe que o generator do Gradio consome via `yield`,
mostrando progresso simples ("Data Gatherer coletando..." → "Quant Analyst
calculando..." → "CIO sintetizando...") em vez de travar a tela por 1-2
minutos. Um dropdown deixa a pessoa escolher a fonte de dados financeiros.

```bash
python app.py
```

### Deploy

**Render** (ativo): Web Service Python, free tier, conectado direto ao
GitHub (redeploy automático a cada push na `main`). Requer `.python-version`
fixando `3.11.9` — o crewai não suporta Python 3.14+, e algumas plataformas
usam Python mais recente por padrão. Secrets configurados nas Environment
Variables do Render: `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `FMP_API_KEY`.

**Hugging Face Space** (pausado): sincronizado automaticamente do GitHub via
GitHub Actions (`.github/workflows/sync-to-hf-space.yml`, `git push` direto
pro remote do Space — não usa a action `hub-sync`, que tenta recriar o repo
via API e esbarra no paywall de CPU básica). Para reativar: trocar o
hardware do Space de volta pra CPU basic (exige assinatura PRO hoje) e
conferir se os secrets `DEEPSEEK_API_KEY`/`GROQ_API_KEY`/`FMP_API_KEY` ainda
estão configurados nas Settings do Space.

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
- **yfinance é scraping, não API oficial**: funciona bem localmente, mas
  a Yahoo Finance bloqueia IPs de datacenter conhecidos (Render, Streamlit
  Cloud). Um provider alternativo autenticado (FMP) resolveu isso sem
  custo, e virou uma feature real (escolha de fonte de dados) em vez de só
  um workaround.
- **Versão do Python importa mais do que parece**: crewai exige
  `>=3.10,<3.14`. Plataformas (Render) e até o mesmo Codespace após um
  rebuild podem vir com uma versão default fora dessa faixa — o
  `.python-version` no repo é a forma mais portátil de fixar isso.
- **Políticas de provedores de nuvem mudam sem aviso**: tanto o Groq
  (rate limits por modelo) quanto a Hugging Face (CPU básica exigindo PRO)
  mudaram durante o desenvolvimento deste projeto. Vale sempre confirmar o
  estado atual antes de assumir "free tier" como garantido.
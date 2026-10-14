---
title: Financial Analyst Agent
emoji: 📈
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
pinned: false
---

# Financial Analyst Crew

Sistema multi-agente de análise financeira autônoma, usando CrewAI, um LLM de
raciocínio (DeepSeek V4 Flash em modo thinking, com fallback automático para
Groq gpt-oss-120b) e integração de ferramentas via Model Context Protocol
(MCP).

Projeto de portfólio — foco em validação dos dados Yahoo e resiliência dos
modelos de IA, não em precisão financeira real (ver disclaimers
gerados pelo próprio relatório).

🔗 **App no ar (Render):** [financial-analyst-agent-crewai.onrender.com](https://financial-analyst-agent-crewai.onrender.com)
*(free tier — a primeira requisição após inatividade pode levar 30-60s pra "acordar")*

📦 **Space na Hugging Face:** pausado por decisão consciente — hospedar
Gradio/Docker em CPU básica passou a exigir assinatura PRO na HF (mudança de
política, julho/2026). Reativar quando o upgrade for feito; nenhum código
precisa mudar para isso.

## Migração gradual da interface

Arquitetura aprovada: React + TypeScript, FastAPI e análise financeira em Python.
A etapa 1 separa resultado estruturado, progresso e apresentação, mantendo Gradio.
A etapa 2 adiciona a API local FastAPI para iniciar e acompanhar análises.
A tabela aparece assim que a coleta termina, antes da interpretação por IA.

- [API local: executar, consultar análises e limites](docs/api-local.md)
- [Planejamento, etapas e contrato interno](docs/plano-migracao-frontend.md)
- [Passo a passo para executar e testar no Windows](docs/executar-e-testar.md)

## Estado atual — Yahoo Finance para ações brasileiras

Os dados financeiros vêm exclusivamente do **Yahoo Finance via yfinance**.
A interface aceita `PETR4` ou `PETR4.SA`; basta informar o código e analisar.
Não há seletor de fonte nem troca automática de provedor financeiro.
Outros mercados e novos provedores ficam para uma etapa posterior.

### Validação e apresentação

- Preços devem ser finitos e positivos, com símbolo correspondente e moeda BRL
  confirmada. Não há moeda padrão nem conversão cambial presumida.
- A data da cotação vem do Yahoo; a hora da consulta fica separada. Quando a
  fonte não informar a data, isso aparece explicitamente.
- Os demonstrativos usam campos padronizados, valores em unidades da moeda
  reportada e exercícios anuais. Lucro por ação usa moeda por ação.
- A base essencial exige receita, lucro líquido, patrimônio dos acionistas,
  caixa operacional e caixa livre no mesmo exercício anual e moeda conhecida.
- `complete`: essa base tem até 550 dias e cotação BRL de até 7 dias,
  compatível com a moeda dos demonstrativos.
- `partial`: há dados úteis, mas algum desses critérios não foi atendido.
- `unavailable`: nenhum dado foi aceito. O cliente recebe avisos, sem dados
  inventados ou consulta a outra fonte financeira.

Os limites são em dias corridos, sem garantia de tempo real. NaN/infinito viram
`null`; zeros e negativos contábeis são preservados. Uma falha em um demonstrativo
não apaga os demais. A tabela é produzida diretamente pelo código, com números
em formato brasileiro, períodos, moeda, origem e limitações.

### Fluxo

```text
Código B3 → Yahoo Finance → validação e contrato de dados
    → tabela determinística para o cliente
    → agentes: dados validados + notícias via MCP → análise → interpretação
```

Os agentes recebem a mesma base exibida ao cliente. A busca de notícias continua
usando `ddgs`; DeepSeek/Groq continuam responsáveis pela interpretação. Se a IA
falhar, a tabela permanece disponível. Sem dados financeiros, não chamamos a IA.

### Executar e testar

O ambiente oficial usa **Python 3.13.9** e **uv 0.11.33**. As dependências
diretas estão em `pyproject.toml`; `uv.lock` fixa as versões transitivas e os
hashes dos arquivos. `requirements.txt` é uma exportação gerada para serviços
que instalam com pip; não deve ser editado manualmente.

```bash
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python test_tools.py PETR4
uv run --locked python app.py
```

Veja [como preparar, reproduzir e atualizar o ambiente](docs/ambiente-desenvolvimento.md)
e [o guia de execução no Windows](docs/executar-e-testar.md). O grupo `dev` inclui `httpx2` para os testes HTTP; `unittest` vem com o Python.

A suíte automatizada não chama APIs externas. `test_tools.py` é um teste manual
online das ferramentas. Yahoo não requer chave no aplicativo; a interpretação
precisa de `DEEPSEEK_API_KEY` e `GROQ_API_KEY`.

O MCP permanece limitado a `mcp<2`. O contrato público agora é v3.0:
`get_financial_statements(ticker, market="BR")`, sem argumento `provider` nem
campo `selection`. Mantivemos `provider_used` para registrar a origem dos dados.
Veja [o contrato B3](docs/contrato-b3.md) para os campos e critérios completos.

`create_files.sh` foi desativado: era um gerador antigo que sobrescrevia o
projeto com versões obsoletas. Use os arquivos versionados e os comandos acima.

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
  versão do CrewAI, que o campo nativo `mcps`). A coleta Yahoo ocorre antes dos agentes; o Data Gatherer recebe
  o snapshot normalizado e apenas a ferramenta de notícias.

```bash
python agents.py PETR4          # Yahoo Finance
```

## Etapa 3 — Interface Gradio (`app.py`)

`crew.kickoff()` é bloqueante, então a execução roda numa thread separada.
`run_analysis_result` publica estados estruturados, consumidos pelo Gradio via
fila. A tabela aparece após a coleta e permanece durante a interpretação.
`presentation.py` transforma esses estados em Markdown; `run_analysis` mantém
compatibilidade com consumidores do relatório textual. A interface usa somente
Yahoo Finance e pede apenas o código da ação.

```bash
python app.py
```

### API local (migração — etapa 2)

```bash
uv run --locked uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs. Use POST /analyses para iniciar e
GET /analyses/{id} para acompanhar; GET /health verifica a API. Execute um único
processo: os registros ficam em memória e são perdidos em reinícios.
Veja [o guia da API](docs/api-local.md) para limites, estados e testes.

### Deploy

**Render** (ativo): Web Service Python, free tier, conectado direto ao
GitHub (redeploy automático a cada push na `main`). O projeto agora fixa Python `3.13.9` em `.python-version`. Ao publicar esta
alteração, confira se a configuração do serviço usa essa mesma versão; variáveis
de ambiente da plataforma podem prevalecer sobre o arquivo. Use instalação por
`uv sync --locked --no-dev` ou `python -m pip install --require-hashes -r requirements.txt`.
A publicação em nuvem desta configuração ainda precisa ser validada. Secrets configurados nas Environment
Variables do Render: `DEEPSEEK_API_KEY`, `GROQ_API_KEY`.

**Hugging Face Space** (pausado): sincronizado automaticamente do GitHub via
GitHub Actions (`.github/workflows/sync-to-hf-space.yml`, `git push` direto
pro remote do Space — não usa a action `hub-sync`, que tenta recriar o repo
via API e esbarra no paywall de CPU básica). Para reativar: trocar o
hardware do Space de volta pra CPU basic (exige assinatura PRO hoje) e
conferir se os secrets `DEEPSEEK_API_KEY`/`GROQ_API_KEY` ainda
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
  Cloud). O fluxo atual sinaliza indisponibilidade e preserva dados parciais;
  não promete disponibilidade contínua do Yahoo.
- **Versão do Python importa mais do que parece**: crewai exige
  `>=3.10,<3.14`. Este projeto padroniza uma faixa mais estreita, Python 3.13,
  com patch 3.13.9 selecionado em `.python-version` e na integração contínua.
  A escolha acompanha o ambiente local testado; alterar Python exige validar
  novamente o lock e os testes.
- **Políticas de provedores de nuvem mudam sem aviso**: tanto o Groq
  (rate limits por modelo) quanto a Hugging Face (CPU básica exigindo PRO)
  mudaram durante o desenvolvimento deste projeto. Vale sempre confirmar o
  estado atual antes de assumir "free tier" como garantido.

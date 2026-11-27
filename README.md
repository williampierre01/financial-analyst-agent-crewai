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


# Analista · Ações brasileiras

Aplicação de portfólio para consultar fundamentos de ações brasileiras, conferir
indicadores e ler uma interpretação assistida por IA. Combina React + TypeScript,
FastAPI, Python e agentes CrewAI, com dados financeiros e interpretação apresentados
separadamente.

**[Acessar o aplicativo no Render](https://financial-analyst-agent-crewai.onrender.com)**
— acesso restrito a contas autorizadas. Após inatividade, o serviço pode demorar
mais para responder.

> Demonstração técnica, não recomendação de investimento. Os dados podem ser
> parciais e não constituem auditoria. Fontes, datas e limitações acompanham a consulta.

## O que já está disponível

- Consulta por código B3, como `PETR4` ou `VALE3`, com cotação, data de referência
  e horário da consulta separados.
- Demonstrativos anuais lado a lado, com moeda, valores integrais ou em milhões,
  zeros e valores negativos preservados. Ausência de informação não vira zero.
- Até três destaques: ROE sobre patrimônio de encerramento, lucro informado/receita
  e dívida/patrimônio. Detalhes expansíveis mostram fórmulas, operandos, fontes,
  períodos e motivos para cálculos indisponíveis.
- Interpretação com notícias e limitações. A tabela e os indicadores continuam
  disponíveis quando o serviço de IA falha.
- Aviso de seções ausentes no relatório. É uma verificação estrutural, não uma
  certificação da precisão financeira ou das notícias.
- Login Firebase, autorização por usuário e sessões controladas pelo backend.
- Registro de tentativas e consumo informado pelos provedores, com diagnóstico
  distinto para timeout, conexão, limites de uso e outras falhas reconhecidas.

**Estado em 27/11/2026:** PRs #36 (indicadores e evidências) e #37 (diagnóstico de
falhas) incorporados. Commit `b89be0f` confirmado como Live no Render. O novo
diagnóstico não elimina indisponibilidades do provedor nem identifica retroativamente
a causa de falhas antigas.

## Arquitetura e serviços

| Camada | Implementação / serviço | Papel |
|---|---|---|
| Interface | React, TypeScript e Vite | Consulta, demonstrativos, indicadores e relatório |
| API | FastAPI e Python | Autenticação, criação e acompanhamento das análises |
| Orquestração | CrewAI | Etapas Data Gatherer → Quant Analyst → CIO |
| Dados financeiros | Yahoo Finance via `yfinance` | Cotação e demonstrativos anuais |
| Notícias | `ddgs`, acessado via MCP | Contexto de notícias com ressalvas de verificação |
| IA | Gemini, DeepSeek ou Groq, configuráveis | Interpretação da base fornecida |
| Identidade | Firebase Authentication | Autenticação das contas |
| Banco | PostgreSQL no Neon | Autorização, sessões e eventos de segurança |
| Publicação | Render | Interface e backend na mesma origem |

As consultas de produção observadas recentemente utilizaram **Gemini**. Isso é
configuração do ambiente: os padrões do código continuam DeepSeek seguido de Groq.
A alternativa só é usada quando configurada. Chaves e seleção dos provedores ficam
no servidor; veja [configuração e medição de IA](docs/provedores-ia.md).

```text
Código B3 → Yahoo Finance → validação dos dados
                              ├─ demonstrativos e indicadores → interface
                              └─ agentes + notícias via MCP → interpretação
```

As análises ficam temporariamente **em memória**, com expiração; reinícios podem
removê-las. O PostgreSQL ainda não armazena um histórico de resultados. Execute
um único processo da API enquanto esse armazenamento permanecer em memória.

## Dados, evidências e limites

A fonte financeira principal é Yahoo Finance; não há troca automática para outra
fonte. A base recebe classificação `complete`, `partial` ou `unavailable` segundo
os critérios do [contrato B3](docs/contrato-b3.md). Esses estados indicam cobertura
e atualidade segundo regras do projeto, não garantia de exatidão ou tempo real.

- Cotação e demonstrativos podem usar moedas diferentes. Não há conversão cambial
  automática; o P/L fica indisponível quando as moedas são incompatíveis.
- Lucro informado pelo provedor não é tratado automaticamente como lucro
  consolidado total. A razão lucro/receita não equivale necessariamente à margem
  líquida consolidada.
- ROE informa a convenção utilizada. O cálculo pela média de dois saldos anuais,
  quando disponível, não representa uma média ponderada ao longo do ano.
- Fluxo de caixa livre é a medida do provedor, com fórmula não conciliada; não é
  apresentado como caixa disponível para dividendos.
- Resultado operacional reportado possui uma exceção documental aprovada para
  PETR4 e VALE3, exercícios 2025/2024, com referências oficiais nos Form 20-F.
  A revisão tem alcance limitado, não constitui auditoria e não libera outros
  períodos automaticamente. O campo operacional legado não conciliado continua
  bloqueado. Veja [integração documental](docs/integracao-operacional-2026-11-26.md).
- Notícias podem vir de resumos de busca; datas normalizadas não comprovam a
  publicação original. O relatório explicita essa limitação.
- Valores isolados não demonstram eficiência operacional nem causas de variação.
  Não há projeção DCF sem premissas, recomendação de compra/venda ou promessa de retorno.

## Ambiente e testes locais

Versões de referência: **Python 3.13.9**, **uv 0.11.33**, **Node 22.17.1** e
**npm 10.9.2**. `uv.lock` e `frontend/package-lock.json` fixam as dependências.
`requirements.txt` é uma exportação gerada; não deve ser editado manualmente.

Na raiz do repositório:

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
uv run --locked python -m backend.api.export_schema --check
```

Para a interface, em sequência:

```powershell
cd frontend
npm.cmd ci
npm.cmd run format:check
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd test
npm.cmd run test:integration
```

Os testes automatizados usam simulações para IA e serviços externos. Não exigem
chaves reais de IA nem consultas financeiras. Testes específicos de PostgreSQL
precisam de banco de teste separado; sem configuração, são ignorados. **Nunca use
o banco de produção para testes.** É possível executar os demais testes sem Docker.
A instalação das dependências e dos navegadores requer acesso à rede.

Execute as suítes de interface e integração uma por vez para evitar conflito nos
artefatos temporários. Na validação local do PR #37, 163 testes Python passaram e
3 de PostgreSQL foram ignorados; o CI do PR foi aprovado. Esses números são um
registro daquela versão, não uma garantia sobre execuções futuras.

## Executar o aplicativo

Antes de iniciar a API real, configure Firebase, autorização no PostgreSQL e
variáveis do servidor conforme o [guia de autenticação](docs/login-firebase-neon.md).
A API isolada também exige autenticação; iniciar o servidor não libera acesso.
Não envie credenciais do backend ao navegador nem as versione.

Terminal 1, na raiz:

```powershell
uv run --locked uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

Abra [localhost:5173](http://127.0.0.1:5173). O Vite encaminha `/api` para a API
local. A configuração de autenticação e origem deve corresponder ao ambiente.
Os guias antigos de HTTP Basic não descrevem a proteção atual.

`test_tools.py PETR4` consulta serviços externos; `agents.py PETR4` também pode
consumir IA. Esses comandos não fazem parte da validação offline. Para economizar
uso, priorize testes simulados e, quando necessária, uma consulta real controlada.

O Gradio (`app.py`) permanece como interface auxiliar legada, fora do fluxo
principal de autenticação do servidor unificado. Não o exponha como substituto
protegido da aplicação React. A publicação principal é no Render; o Space da
Hugging Face permanece pausado, sem compromisso de reativação nesta etapa.

## Próximas etapas

- Histórico persistente de análises por usuário, com isolamento de acesso e
  reabertura sem nova chamada de IA, sempre preservando a data original.
- Refinamentos de síntese e apresentação, mantendo fontes e incertezas explícitas.
- Ampliar verificações de autenticação e acompanhar falhas reais pelos registros,
  sem repetir consultas apenas para testar apresentação.

Esses itens são planejamento, não funcionalidades já entregues. Conversão cambial,
novas fontes e novos mercados exigem escopo e validação próprios.

## Documentação

- [Estado atual](docs/estado-atual.md) e [continuidade](docs/continuidade-projeto.md)
- [Plano geral](docs/plano-geral-desenvolvimento.md)
- [Contrato de dados B3](docs/contrato-b3.md)
- [Provedores de IA, tentativas e consumo](docs/provedores-ia.md)
- [Firebase, Neon e autorização](docs/login-firebase-neon.md)
- [Ambiente reproduzível](docs/ambiente-desenvolvimento.md)
- [Pendências de homologação](docs/pendencias-homologacao.md)

Alguns guias preservam instruções e decisões históricas. Para o estado publicado,
considere o resumo datado mais recente e este README; restrições antigas de testes
locais e instruções de HTTP Basic não substituem o fluxo atual descrito aqui.

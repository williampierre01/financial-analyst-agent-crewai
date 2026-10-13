# Contrato B3 — versão 3.0 — Yahoo Finance

## Entrada e origem

`get_financial_statements(ticker, market="BR")` aceita códigos como `PETR4`,
`VALE3` e `ITUB4`, com ou sem `.SA`. Outros mercados são rejeitados antes da
consulta. O formato do código não prova a existência ou a classe do ativo:
o símbolo retornado pelo Yahoo também deve corresponder. Não há substituição
por ADRs, seleção de fonte nem uso de credenciais de provedores financeiros.

Esta versão remove `provider` da chamada e `selection` da resposta v2.
Clientes anteriores devem remover esses argumentos e acessos.

## Saída

`schema_version=3.0`, `ticker`, `display_ticker`, `market`, `exchange`,
`retrieved_at`, `provider_used`, `quote`, `statements`,
`fundamentals_available`, `common_period`, `status` e `warnings`.

`provider_used` é `yfinance` quando há dados úteis; sem dados, é `null`.
A tabela informa Yahoo Finance como a fonte consultada, inclusive na falha.

`quote` inclui preço positivo/finito, moeda BRL confirmada, fonte, `as_of`
em UTC ou `null` e `freshness` (`recent`, `stale`, `unknown`). A hora da consulta
nunca substitui a data da cotação. Datas futuras acima de cinco minutos são
descartadas. Moeda dos demonstrativos é independente da moeda de negociação.

`statements` contém `income_statement`, `balance_sheet` e `cash_flow`.
Cada grupo tem até dois exercícios anuais em ordem decrescente, com:
`period_end`, `period_type=annual`, `currency`, `source=yfinance`,
`unit=currency_units`, `per_share_fields`, `values` e `missing_fields`.
Datas inválidas/futuras e registros sem identidade/período confirmado são
descartados. Moeda desconhecida permanece `null` e impede o alinhamento.

| Grupo | Campo comum | Campo Yahoo |
|---|---|---|
| DRE | revenue | Total Revenue |
| DRE | net_income | Net Income |
| DRE | operating_income | Operating Income |
| DRE | diluted_eps | Diluted EPS |
| Balanço | total_assets | Total Assets |
| Balanço | stockholders_equity | Stockholders Equity |
| Balanço | total_debt | Total Debt |
| Balanço | cash | Cash And Cash Equivalents |
| Caixa | operating_cash_flow | Operating Cash Flow |
| Caixa | free_cash_flow | Free Cash Flow |

Valores estão em unidades da moeda reportada; EPS é moeda por ação. Não há
conversão, interpolação ou substituição entre conceitos diferentes de patrimônio.
NaN e infinito viram `null`; zero e negativos contábeis são preservados.

## Qualidade

`fundamentals_available` exige receita, lucro líquido, patrimônio dos acionistas,
caixa operacional e caixa livre no mesmo exercício anual e na mesma moeda.
Isso não garante todos os dados ou denominadores necessários a cada indicador.

- `complete`: base essencial com até 550 dias e cotação BRL com até 7 dias,
  na mesma moeda dos demonstrativos.
- `partial`: dados úteis, mas sem todos os critérios acima.
- `unavailable`: nenhum dado aceito.

Os limites são em dias corridos, sem calendário de pregões ou garantia de tempo
real. Falhas parciais preservam os demais dados; falhas totais retornam avisos,
sem mudar de fonte. Mensagens internas de exceção não são exibidas ao cliente.

## Apresentação e agentes

Tabela fixa em português, com milhar por ponto, decimal por vírgula, valores
ausentes explícitos, moeda, período, origem, datas e avisos. Os números da tabela
não são gerados pela IA. O mesmo snapshot é entregue aos agentes; eles acessam
apenas notícias via MCP. Falhas de interpretação não apagam a tabela.

A busca de notícias usa `ddgs`. Os modelos DeepSeek/Groq são separados da fonte
financeira. Cálculos da interpretação ainda dependem de IA; torná-los
determinísticos será uma etapa posterior.

## Futuras extensões

O contrato separa a coleta dos campos comuns. Novos provedores ou mercados
serão avaliados depois da consolidação do Yahoo, com validação de identidade,
moeda, períodos, cobertura e limites antes de habilitar qualquer seleção.

[Referência dos demonstrativos do yfinance](https://ranaroussi.github.io/yfinance/reference/yfinance.financials.html)

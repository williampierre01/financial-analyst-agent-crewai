# Diagnóstico financeiro — PETR4 e VALE3

16/11/2026. Escopo documental: exercícios anuais 2025/2024, USD milhões.
Base de código: `c3668b2`. Não altera contratos, números ou bloqueios.
Valores do aplicativo são das capturas e do registro de homologação; não houve
nova coleta Yahoo nesta rodada nem chamada de IA. Não são dados atuais garantidos.

## Evidências e definições

Fontes primárias consultadas:

- [Petrobras, Form 20-F 2025](https://petrobras.com.br/documents/2677942/17808296/FORM%2B20F%2B2025%2BEN.pdf/3b6371b3-900d-ae05-294d-f9acd9d8b26e?download=true&t=1777312960000&version=1.0), páginas impressas 173–174 e 189–190.
- [Vale, Form 20-F 2025](https://vale.com/documents/d/guest/form-20-f-2025-en), página impressa 115, tabela de resultados; seção Liquidity and Capital Resources para caixa operacional.

| Empresa / item | Aplicativo 2025 / 2024 | Documento oficial 2025 / 2024 | Diagnóstico |
|---|---:|---:|---|
| Petrobras / receita | 89.195 / 91.416 | 89.195 / 91.416 | Coincide na amostra |
| Vale / receita | 38.403 / 38.056 | 38.403 / 38.056 | Coincide na amostra |
| Petrobras / lucro líquido | 19.634 / 7.528 | Atribuível: 19.634 / 7.528; consolidado: 19.720 / 7.605 | Rótulo genérico omite o perímetro |
| Vale / lucro líquido | 2.352 / 6.166 | Atribuível: 2.352 / 6.166; consolidado: 1.983 / 5.975 | Mesmo problema de definição |
| Petrobras / operacional histórico bloqueado | 27.758 / 25.691 | 26.113 / 26.876 | Não conciliado |
| Vale / operacional histórico bloqueado | 11.343 / 11.101 | 5.897 / 10.788 | Não conciliado |
| Petrobras / caixa operacional | 36.047 / 37.984 | 36.047 / 37.984 | Coincide na amostra |
| Vale / caixa operacional | 8.801 / 9.366 | 8.801 / 9.366 | Coincide na amostra |
| Petrobras / fluxo de caixa livre | 16.526 / 23.340 | 16.528 / 23.318 | Definições distintas |

Petrobras: caixa operacional menos aquisição de imobilizado/intangível
(19.521 / 14.644) reproduz os valores do app. A reconciliação oficial inclui
também participações societárias (+2 / −22 no quadro), chegando ao FCF oficial.
Isso explica aritmeticamente esta amostra; não comprova metodologia universal do Yahoo.

## O que o código efetivamente faz

- `financial_data.py`: mapeia `Net Income` como `net_income`, rotulado “Lucro líquido”; bloqueia qualquer `Operating Income` numérico antes da geração do relatório. Não há substituição pelo EBIT, EBITDA ou valor oficial.
- `yahoo_statements.py`: conserva moeda e exige período 12M e símbolo correspondente. Isso valida o contrato, não a definição contábil do fornecedor.
- `verified_metrics.py`: divide o lucro recebido pela receita e chama o resultado de “Margem líquida”. Na amostra, trata-se de lucro atribuível dividido pela receita consolidada. Não é a margem baseada no lucro consolidado total.
- ROE usa patrimônio dos acionistas; confirmar seu perímetro junto ao lucro antes de afirmar comparabilidade. A média de dois encerramentos já é identificada como aproximação.
- FCF vem pronto do fornecedor: o aplicativo não coleta operandos para verificar sua fórmula. Dívida total também precisa de decomposição (empréstimos, arrendamentos e demais itens), não de comparação direta com dívida líquida.

## Resultado operacional: causa ainda não demonstrada

Os documentos oficiais esclarecem a linha desejada, mas não fornecem a ponte
para a normalização do Yahoo. Na Vale, o diferencial de 2025 é 5.446; retirar
apenas impairment/alienações de 4.599 não o explica. Não concluir que o campo
é “ajustado”, EBITDA ou livre de não recorrentes por aproximação numérica.
Não há justificativa para liberar o campo nem corrigir valores por ticker/ano.

Para concluir: obter um snapshot bruto datado do fornecedor com componentes
de receita, custos, despesas, impairment, alienações, equivalência e financeiro;
registrar moeda/unidade/perímetro; confrontar a definição publicada do fornecedor
e reconciliar cada parcela com as notas oficiais nos dois exercícios.
Se essa ponte não puder ser documentada, manter o bloqueio ou propor outra fonte.

## Correção proposta e recorte autorizado

Após aprovação, o recorte implementado identifica valores como informados pelo
provedor e explicita a incerteza de perímetro/fórmula. A razão foi renomeada para
lucro informado/receita. Não foram criados campos de lucro consolidado/atribuível,
nem verificação automática por documento: isso exige coleta e contrato próprios.
Os itens abaixo são o plano completo, parcialmente atendido por esse recorte.

1. Distinguir lucro atribuível e consolidado no contrato e nos rótulos. Para os demais ativos, não inferir o perímetro apenas porque PETR4/VALE3 coincidem.
2. Explicitar o numerador da margem; conservar a convenção atual com nome preciso ou introduzir margem consolidada somente com campo próprio validado. Não trocar silenciosamente números.
3. Identificar FCF como métrica do fornecedor, com fórmula não conciliada quando faltarem operandos; não apresentá-lo como o FCF oficial da companhia.
4. Manter operacional e múltiplos entre moedas bloqueados. Anotar por campo motivo, evidência e versão da regra; nunca usar números fixos como correção.

Critérios de testes para a futura implementação: perímetros não intercambiáveis;
valores ausentes não viram zero; moeda/período/unidade incompatíveis bloqueiam
cálculos; FCF preserva sinais e declara componentes; guardas operacionais seguem
ativas; relatórios e interface usam as mesmas definições. Fixtures precisam de
proveniência e valores esperados independentes da implementação.

Limites: EPS e sua base de ações, dívida, balanço integral, reapresentações,
comparabilidade entre empresas e FCF oficial da Vale não auditados nesta rodada.
Não executar uma alteração de dados até definir o escopo da correção.

## Nova coleta do fornecedor — 16/11/2026

Consulta pública, sem IA, para PETR4.SA e VALE3.SA. Respostas HTTP 200,
com moeda USD e períodos anuais. Resposta bruta e URL de consulta preservadas
em `evidencias/yahoo-operating-2026-11-16.json`; o horário UTC consta no arquivo.
Nenhum cookie ou cabeçalho de autenticação foi incluído.
Esta coleta substitui a limitação de ausência de snapshot descrita na abertura.

Valores abaixo em USD milhões, na ordem 2025 / 2024:

| Campo Yahoo | Petrobras | Vale |
|---|---:|---:|
| OperatingIncome | 27.758 / 25.691 | 11.343 / 11.101 |
| TotalOperatingIncomeAsReported | 26.113 / 26.876 | 5.897 / 10.788 |
| GrossProfit | 42.459 / 45.972 | 13.456 / 13.791 |
| OperatingExpense | 14.701 / 20.281 | 2.113 / 2.690 |

O campo `TotalOperatingIncomeAsReported` coincide com os documentos oficiais
citados acima nas quatro observações. `OperatingIncome` é igual a GrossProfit
menos OperatingExpense nas quatro observações, mas não representa a mesma linha.
Isso demonstra a divergência de campos nesta amostra, não uma definição universal.

Na Vale, a ponte aritmética fecha:

- 2025: 11.343 − 4.599 (ImpairmentOfCapitalAssets) − 847 (OtherSpecialCharges) = 5.897.
- 2024: 11.101 − (−301) − 614 = 10.788.
- `SpecialIncomeCharges` é −5.446 / −313, exatamente a diferença entre os campos.

A identidade fecha dentro dos dados Yahoo. A classificação detalhada de
OtherSpecialCharges nas notas oficiais ainda precisa de comprovação; não chamar
esse resultado de auditoria nem classificar automaticamente todo item como não recorrente.

Na Petrobras, as diferenças são +1.645 / −1.185 (OperatingIncome menos reportado).
Ainda não há ponte documentada por componente. As classificações de despesas
Yahoo diferem das linhas oficiais; não somar subtotais e componentes indiscriminadamente.

Decisão: manter o bloqueio atual. O campo reportado é candidato para uma coleta
separada com proveniência, moeda, período, ausência e validação explícitos, sem
fallback para OperatingIncome/EBIT/EBITDA. A coincidência em duas empresas não
autoriza liberação para todo o mercado. Nenhum código de produção foi alterado.

Próxima etapa: documentar a composição Petrobras e a definição do fornecedor;
preparar contrato e testes para o campo reportado somente com critérios de aceite
claros. O diagnóstico não depende de Docker, Neon ou chamadas de IA.

## Petrobras: ponte pelos totais conciliada — 16/11/2026

Fonte adicional: [demonstrações Petrobras arquivadas na SEC](https://www.sec.gov/Archives/edgar/data/1119639/000129281426000706/pbrfs4q25usd_6k.htm), demonstração de resultado e notas 10–12.

A ponte abaixo utiliza valores assinados, em USD milhões. Os dois caminhos
chegam ao mesmo resultado antes dos impostos; não é uma decomposição completa
da metodologia de normalização do fornecedor.

| Componente | 2025 | 2024 |
|---|---:|---:|
| Yahoo OperatingIncome | 27.758 | 25.691 |
| Yahoo OtherIncomeExpense | 2.984 | −10.542 |
| Yahoo NetNonOperatingInterestIncomeExpense | −3.947 | −4.007 |
| Soma / PretaxIncome | 26.795 | 11.142 |
| Menos resultado financeiro oficial | −734 | +15.107 |
| Menos equivalência patrimonial oficial | +52 | +627 |
| Resultado operacional oficial / Yahoo reportado | 26.113 | 26.876 |

Portanto, o ajuste entre operacional Yahoo e reportado é −1.645 em 2025 e
+1.185 em 2024. O resíduo desta ponte é zero nos dois anos. Não se trata de
simples exclusão de impairment, nem há fundamento para substituir pelo EBIT.

As notas oficiais mostram que o financeiro inclui mais que juros. A coincidência
entre resultados antes dos impostos permite conciliar os agregados, mas não prova
como cada rubrica foi redistribuída pelo fornecedor. Essa rastreabilidade detalhada
continua pendente; não apresentar a ponte como auditoria integral.

A [ajuda oficial Yahoo](https://help.yahoo.com/kb/SLN37694.html), localizada na busca,
informa mudança do conjunto de dados Morningstar e de rótulos. A abertura retornou
HTTP 429. Isso não fornece um contrato para os identificadores do endpoint usado
pelo aplicativo: não presumir equivalência entre nomes da interface e campos API.

### Resultado da investigação e critério para a próxima implementação

- Divergência reproduzida e pontes aritméticas verificadas em Petrobras e Vale,
  nos dois exercícios. Campo reportado coincide nas quatro observações.
- Pendente: definição formal do identificador, rastreabilidade das reclassificações
  e cobertura além desta amostra. O campo atual permanece bloqueado.
- Próximo recorte seguro: coletar o campo reportado separadamente, conservando o
  bloqueio de apresentação e de uso pela IA enquanto sua validação não for explícita.
  Ausência não vira zero; não usar fallback para OperatingIncome, EBIT ou EBITDA.
- Uma futura liberação exige regra documentada de moeda, unidade, período e
  proveniência e teste de valores ausentes/conflitantes, sem correção fixa por ticker.

Verificação offline reproduzível: `python scripts/check_operating_evidence.py`.
Usa apenas o snapshot público salvo; não acessa rede, banco, Docker ou IA.

## Coletor diagnóstico separado

Implementado `operating_evidence.py`, fora do fluxo do aplicativo e das ferramentas
MCP/IA. Coleta somente `annualTotalOperatingIncomeAsReported`, sem fallback.
Preserva zeros e negativos; rejeita identidade/período inválidos, moeda desconhecida
ou conflitante e valores não finitos. Duplicatas numéricas conflitantes geram erro.
Todos os resultados têm `validation_status=unverified` e
`eligible_for_analysis=false`; nenhum valor é promovido ao contrato público.

Execução opcional (consulta Yahoo, sem IA), na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe operating_evidence.py PETR4 --output ../petrobras-reported.json --cache-dir ../.yahoo-diagnostic-cache
```

O arquivo de saída precisa ser novo. O comando não é executado automaticamente
pelo servidor. Nesta etapa, validação por respostas simuladas; o snapshot real da
investigação anterior permanece como evidência. A interface e seu bloqueio não mudam.

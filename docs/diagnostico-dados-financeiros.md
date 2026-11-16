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

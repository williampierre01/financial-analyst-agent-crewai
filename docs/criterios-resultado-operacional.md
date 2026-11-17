# Critérios para o resultado operacional reportado

Definidos em 17/11/2026. Especificação da próxima implementação; não libera
valores nem altera o comportamento publicado pelo PR #31.

## Escopo

Validar cada observação anual individualmente. A coincidência de PETR4/VALE3 em
2025/2024 não autoriza outros períodos ou empresas. Não criar uma lista de tickers
automaticamente aprovados. O campo normalizado `OperatingIncome` segue bloqueado.

## Condições obrigatórias

1. Origem exata `annualTotalOperatingIncomeAsReported`, com símbolo, data de coleta
   e evidência preservados. Nunca substituir por OperatingIncome, EBIT ou EBITDA.
2. Valor finito, moeda conhecida, unidade monetária explícita e período anual
   encerrado, sem data futura. Zero e negativo são valores válidos; ausência não é zero.
3. Documento oficial identificável por URL, versão/data e página/tabela, com empresa,
   período, moeda, escala e perímetro contábil correspondentes. Conversão de escala
   é permitida e registrada; conversão cambial não é presumida.
4. Linha oficial de resultado operacional identificada por seu significado contábil,
   não apenas pelo nome. Medida ajustada, resultado por segmento ou outro perímetro
   não substituem o resultado consolidado. A revisão precisa registrar essa decisão.
5. Comparação com valor oficial independente da resposta Yahoo. Para documento
   arredondado, usar no máximo metade da menor unidade apresentada, convertida à
   unidade-base, registrando a precisão. Sem tolerância percentual genérica.
6. Ausência de duplicatas conflitantes e reapresentações não resolvidas. Mudança de
   valor, moeda, período ou versão da evidência invalida a aprovação anterior.
7. Registro de revisão com responsável, data, versão da regra, referências e
   identificação dos conteúdos examinados. Um booleano informado pelo cliente ou
   uma conclusão de IA não constitui aprovação.

Uma divergência do campo normalizado não reprova automaticamente o campo reportado:
este deve ser confrontado diretamente com a linha oficial. As pontes aritméticas
ajudam a investigação, mas não substituem os requisitos acima.

## Estados e comportamento

| Estado por observação | Significado | Uso no aplicativo/IA |
|---|---|---|
| Não verificado | Falta documento, revisão ou comprovação de perímetro | Bloqueado |
| Rejeitado | Incompatibilidade, conflito ou diferença fora da precisão documentada | Bloqueado |
| Validado | Todos os requisitos atendidos para a evidência exata revisada | Candidato à futura integração |

Separar validação documental de atualidade: um exercício antigo pode estar correto
e continuar sujeito às regras de idade dos demonstrativos. Validar uma observação
não aprova outra, nem libera múltiplos com moedas incompatíveis.

## Contrato proposto

Manter evidências fora do contrato público enquanto não houver integração testada.
Cada observação deve registrar: campo de origem, símbolo, período, moeda, unidade,
valor, coleta, referência oficial e versão, linha/perímetro, escala, precisão,
valor oficial, diferença, estado, motivo e revisão. A elegibilidade deve ser
derivada desses requisitos, nunca aceita diretamente de uma entrada externa.

A futura interface deverá identificar “Resultado operacional reportado” e sua
fonte. Não sobrescrever silenciosamente o significado do campo antigo. Versionar
o contrato e adaptar consumidores caso a integração altere sua semântica.

## Testes de aceite da próxima implementação

- Correspondência exata e arredondamento no limite e acima do limite.
- Ausência, zero, negativo, booleano, infinito e NaN.
- Símbolo, moeda, escala, período e perímetro incompatíveis; período futuro.
- Duplicatas iguais, conflitantes e reapresentação que revoga validação anterior.
- Documento/revisão ausentes e tentativa de forjar elegibilidade na entrada.
- Aprovação de um ano não libera outro; valor bloqueado não chega à IA/interface.
- Campo reportado ausente não recorre a campos alternativos; demais dados continuam disponíveis.

## Situação atual e próximo recorte

PR #31 incorporado em `b5a1239`, checks aprovados e Live confirmado por captura.
As quatro coincidências e pontes estão documentadas, mas o coletor continua
marcando tudo como não verificado. Não há mecanismo de revisão implementado.

Próximo recorte: implementar e testar um validador offline com evidências oficiais
estruturadas e motivos por observação, ainda sem integração com interface/MCP/IA.
Depois revisar as evidências PETR4/VALE3 por esses critérios. A liberação de uso
fica para uma alteração posterior, com contrato e testes próprios.

Sem Docker, consultas ao banco de produção ou chamadas de IA para essa etapa.

## Implementação offline — 17/11/2026

`operating_validation.py` implementa `validate_observation` e `validate_batch`.
Recebe uma observação achatada (metadados do coletor mais valor/período/moeda),
um registro oficial e revisões locais fornecidas separadamente. Usa Decimal para
escala/precisão e SHA-256 do conteúdo canônico para vincular a revisão à evidência.
Retorna estado, motivo, diferença e tolerância quando calculáveis. Conflitos de
observações ou registros oficiais do mesmo símbolo/período bloqueiam o lote afetado.

O registro oficial exige `document` com URL HTTPS, versão, localização e SHA-256,
`perimeter=consolidated`, `measure=operating_income_reported`, escala, precisão e
`unresolved_restatement=false`. Precisão zero representa valor documental exato;
precisão 1 em escala de milhões permite diferença máxima de 500 mil unidades.
A revisão exige responsável, data com fuso, versão da regra e digest correspondente.

Limite de confiança: o validador verifica consistência das declarações registradas;
não baixa nem autentica documentos, revisores ou a independência da transcrição.
O registro de revisões deve ser mantido localmente por responsável autorizado,
jamais recebido como aprovação do cliente. Nenhuma revisão real de PETR4/VALE3
foi criada nesta implementação; os testes usam documentos e revisores fictícios.
Mesmo `validated` retorna `eligible_for_analysis=false` nesta fase.

Validação: nove testes novos cobrindo arredondamento, valores inválidos, metadados,
perímetro, revisão ausente, flags forjadas, versão alterada, duplicatas e isolamento
entre exercícios. Não há integração com interface, MCP, banco ou IA.

## Evidências oficiais estruturadas — 17/11/2026

`docs/evidencias/operating-review-candidates.json` reúne quatro observações,
PETR4/VALE3 em 2025/2024, extraídas do snapshot já coletado, e transcrições das
linhas oficiais. Inclui URL, versão, localização, moeda, escala, precisão e SHA-256
dos documentos completos baixados. Os originais estão em
`../official-operating-documents/`, fora do Git; não são dependência dos testes.

O pacote não contém revisões aprovadas. `unresolved_restatement=null` indica
que a avaliação de reapresentações ainda não foi encerrada; não indica que uma
reapresentação foi encontrada. As quatro observações permanecem `unverified`.
Próximo passo documental: verificar versões/reapresentações e registrar revisão
humana identificada, vinculada ao conteúdo exato. Não preencher aprovação fictícia.

Revisão de código: documentos malformados são rejeitados; registros de revisão
com data inválida são ignorados, mantendo a necessidade de revisão válida.
Os testes incluem o pacote real e asseguram que não se torne elegível para análise.

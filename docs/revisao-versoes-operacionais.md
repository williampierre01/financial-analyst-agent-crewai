# Revisão de versões oficiais — 17/11/2026

Consulta direta ao endpoint público SEC submissions para CIK 0000917851 (Vale)
e 0001119639 (Petrobras). Resultado filtrado preservado em
`evidencias/sec-submissions-check-2026-11-17.json`, com horário, URL, emissor,
data mínima coberta pela lista recente e números de protocolo.

## Achados

- No recorte desde 01/01/2025 consultado, não foi listado 20-F/A para os dois
  emissores. Isso não exclui correções comunicadas por outros formulários.
- Vale: 20-F de 2025 protocolado em 27/03/2026, 0001292814-26-001844.
- Petrobras: 20-F de 2025 protocolado em 09/04/2026, 0001292814-26-002168.
- Existem 6-K/A. A presença de `/A` não demonstra por si só alteração no
  resultado operacional anual. Datas de referência trimestrais não bastam
  para descartar impactos nos comparativos anuais.

## Documentos adicionais examinados

1. [Vale demonstrações 2024, 6-K/A de fevereiro/2025](https://www.sec.gov/Archives/edgar/data/917851/000129281425000508/valedfifrs4q24_6ka.htm):
   demonstração consolidada informa resultado operacional 2024 de USD 10.788
   milhões, igual ao comparativo de 2024 no 20-F 2025. Há linhas de segmentos
   com anos anteriores identificados como revisados; não confundir essas linhas
   com alteração do total consolidado examinado.
2. [Vale release 2025 emendado, março/2026](https://www.sec.gov/Archives/edgar/data/917851/000129281426000608/valepr4q25_6ka1.htm):
   contém medidas ajustadas. Essas medidas não substituem a linha operacional
   consolidada usada no pacote de candidatos.
3. [Petrobras 2T26 emendado](https://www.sec.gov/Archives/edgar/data/1119639/000129281426004623/pbrfs2q26usd_6ka.htm)
   e [Vale 2T26 emendado](https://www.sec.gov/Archives/edgar/data/917851/000129281426004322/valedfifrs2q26_6ka.htm):
   abertos e pesquisados pelo termo `restat`, sem ocorrência no texto extraído.
   Busca textual negativa não comprova ausência de reapresentação.

## Alcance e pendências

A busca geral na web não foi usada como prova de inexistência. O levantamento SEC
preserva metadados de 20-F, 20-F/A e 6-K/A, mas não examinou integralmente todos os
6-K ordinários, anexos e comunicados de RI/CVM. Falta confrontar os comparativos
Petrobras com o documento anual de 2024 e concluir a revisão de conteúdos emendados
relevantes e eventuais comunicações posteriores aos anuais de 2025.

Portanto, `unresolved_restatement` permanece `null` nos quatro candidatos.
Nenhuma revisão humana foi criada em nome do usuário e nenhuma elegibilidade
foi liberada. Esta é uma verificação documental parcial e rastreável, não uma
certificação de inexistência de reapresentações.

PR #32: merge `c6dc4eb` confirmado no GitHub, checks aprovados; captura do usuário
confirma Live no Render. Sem alteração de código nesta rodada.

## Complemento: comparativo Petrobras e finalidade das emendas

Conferido em 17/11/2026:

- [Petrobras 20-F 2024](https://www.sec.gov/Archives/edgar/data/1119639/000129281425001352/pbrform20f_2024.htm), demonstração consolidada: resultado antes de financeiro, equivalência e impostos de USD 26.876 milhões. Coincide com o comparativo 2024 das demonstrações de 2025. A pendência de confrontar este valor está encerrada.
- Petrobras 2T26, protocolo 0001292814-26-004623: a nota explicativa da emenda informa inclusão do Exhibit 101 (dados interativos), sem outras alterações ao 6-K original. Essa emenda não é evidência de mudança nos valores.
- Vale 2T26, protocolo 0001292814-26-004322: mesma finalidade declarada, inclusão do Exhibit 101, sem outras alterações ao original.
- Vale demonstrações 2024, protocolo 0001292814-25-000508: a nota explica inclusão das assinaturas que haviam sido omitidas no envio, sem alteração das demais informações.

Essas conclusões substituem a mera busca textual negativa registrada acima para
os três documentos. Foram lidas as notas explicativas, não inferida a finalidade
pelo tipo de formulário.

### Pendência delimitada

Os comparativos anuais de 2024 agora coincidem para ambas as empresas. As três
emendas financeiras examinadas acima não alteram os valores segundo suas notas.
Continua sem conclusão a finalidade do release Vale 2025 emendado em março/2026
(0001292814-26-000608): não foi encontrada nota explicativa no texto extraído.
Será necessário comparar seu conteúdo com o original; não equiparar medidas
ajustadas com resultado operacional reportado. A busca não equivale a auditoria
exaustiva de todos os comunicados posteriores de RI/CVM.

O pacote de candidatos continua intacto, sem revisão aprovada. Não há alteração
de código nem necessidade de repetir a suíte de testes por estas notas documentais.

## Comparação do release Vale 4T25: original e duas emendas

Foram baixados e comparados os textos HTML dos protocolos
[0001292814-26-000369](https://www.sec.gov/Archives/edgar/data/917851/000129281426000369/valepr4q25_6k.htm),
[0001292814-26-000375](https://www.sec.gov/Archives/edgar/data/917851/000129281426000375/valepr4q25_6ka.htm) e
[0001292814-26-000608](https://www.sec.gov/Archives/edgar/data/917851/000129281426000608/valepr4q25_6ka1.htm).
Hashes dos três HTML e diferenças de tokens preservados em
`evidencias/vale-release-version-diff.json`. Originais e texto extraído ficam em
`../official-operating-documents/`. Comparação não cobre imagens incorporadas.

Mudanças identificadas no texto:

- Primeira emenda: valor da recompra de debêntures de USD 723 para 703 milhões;
  uma linha da distribuição geográfica passa de 479/5%/78% para 449/4%/90%.
- Segunda emenda: linha Other do segmento níquel, quadro anual 2025 de EBITDA
  ajustado, passa de 195 para 287 milhões; horizonte de uma estimativa de
  desembolsos muda de 2028–2035 para 2029–2035; correção ortográfica adicional.
- Também mudam identificadores do formulário e datas de assinatura.

A emenda contém alterações quantitativas: não deve ser classificada como apenas
formatação. A linha segmentada alterada não é o resultado operacional consolidado
usado nos candidatos. O texto ainda informa reapresentação de apresentação de
streaming por segmento; isso não demonstra alteração do resultado consolidado.

Conclusão delimitada: a comparação textual pendente foi concluída. Não se
identificou nessa comparação alteração das quatro observações anuais candidatas;
isso não certifica todos os anexos/imagens nem todos os comunicados posteriores.
A aprovação documental continua separada e não foi atribuída ao usuário.

## Conferência das imagens — 24/11/2026

Retomada concluída: 114 de 114 imagens disponíveis localmente (38 por versão).
O download inicial voltou a falhar com HTTP 504; uma nova tentativa limitada
concluiu os arquivos restantes. O manifesto `evidencias/vale-release-image-hashes.json`
registra SHA-256 por arquivo, data de conferência e comparação entre versões.
O estado `complete` descreve somente a coleta e comparação dos arquivos.
Não significa aprovação dos dados para análise. Pixels de rastreamento foram excluídos.

Original → primeira emenda: 36 imagens idênticas e duas diferentes. A leitura
visual das páginas 2 e 25 confirma, respectivamente, 723 → 703 milhões na
recompra de debêntures e 479/5%/78% → 449/4%/90% na linha Asia/Others.

Primeira → segunda emenda: 34 imagens de mesmo nome idênticas, três diferentes
(002, 025 e 028), além da substituição de `image_029.jpg` por `image_039.jpg`.
Todos os arquivos diferentes/substituídos foram inspecionados visualmente:

| Página | Evidência observada na segunda emenda | Consequência |
| --- | --- | --- |
| 2 | Imagem mostra 723 milhões; texto HTML continua com 703 milhões. | Divergência entre representações do mesmo documento. |
| 25 | Imagem mostra 479/5%/78%; texto HTML continua com 449/4%/90%. | A correção textual da primeira emenda não está refletida na imagem da segunda. |
| 28 | Correção de `echaracterization` para `decharacterization`, com mudança de resolução; totais de EBITDA ajustado 4T25/4T24 seguem 4.588/3.794 milhões. | Hash diferente não equivale, por si só, a alteração numérica. |
| 29 (arquivo 039) | Other do segmento níquel, EBITDA ajustado anual 2025: 195 → 287 milhões. | Correção numérica segmentada confirmada também na imagem. |

A divergência das páginas 2 e 25 impede tratar texto e imagem como fontes
intercambiáveis. Ela não demonstra alteração do resultado operacional anual
consolidado, mas precisa permanecer explícita na revisão. A mudança textual do
horizonte 2028–2035 → 2029–2035 não teve imagem alterada detectada pelo manifesto;
não atribuir automaticamente essa correção à representação visual.

Conclusão desta etapa: comparação textual e triagem visual das diferenças dos
três releases concluídas. Não se identificou nessas diferenças alteração direta
dos valores operacionais anuais candidatos. Isso não substitui a revisão de
todos os comunicados posteriores, nem resolve automaticamente a condição de
reapresentação dos quatro candidatos. O inventário SEC continua datado de
17/11/2026; não foi atualizado para afirmar cobertura até 24/11/2026.

Próxima etapa delimitada: revisar a vigência dos demonstrativos anuais usados
nos candidatos e registrar a decisão documental com a fonte/versão escolhida.
Até essa decisão, `unresolved_restatement` permanece `null`, o registro de
aprovações permanece vazio e o resultado operacional continua indisponível
para a análise em produção. Nenhum código da aplicação foi alterado nesta etapa.

## Decisão de referência anual — 24/11/2026

Decisão técnica: adotar como referência da próxima revisão as demonstrações
consolidadas dos 20-F de 2025 depositados na SEC, com seus comparativos de 2024.
Isso elimina a dependência do release segmentado para definir este indicador.
Os arquivos foram baixados, preservados e identificados por SHA-256 em
`evidencias/annual-source-verification-2026-11-24.json`. Não houve substituição
silenciosa do pacote anterior de candidatos ou criação de aprovação humana.

| Empresa | Documento de referência | Página | 2025 | 2024 |
| --- | --- | --- | ---: | ---: |
| Petrobras | [20-F 2025, protocolo 0001292814-26-002168](https://www.sec.gov/Archives/edgar/data/1119639/000129281426002168/pbrform20f_2025.htm) | F-4 | 26.113 | 26.876 |
| Vale | [20-F 2025, protocolo 0001292814-26-001844](https://www.sec.gov/Archives/edgar/data/917851/000129281426001844/valeform20f_2025.htm) | F-3 | 5.897 | 10.788 |

Valores anuais consolidados em milhões de USD. Na Petrobras, a medida é o
resultado antes do financeiro líquido, equivalência patrimonial e impostos;
na Vale, a linha é `Operating income`. As quatro observações coincidem com o
snapshot de `annualTotalOperatingIncomeAsReported`. A conferência das tabelas
foi automatizada após a leitura das linhas, com preservação dos arquivos.

### Vigência: o que foi e não foi confirmado

O inventário foi atualizado em 24/11, incluindo agora metadados de 6-K ordinários:
`evidencias/sec-submissions-check-2026-11-24.json`. No recorte desde 01/01/2025,
foram obtidos 379 registros para Vale e 283 para Petrobras. Os últimos anuais
listados continuam sendo os 20-F de 2025 acima; nenhum 20-F/A consta nesse recorte.
Isso confirma a seleção do último protocolo anual listado, não ausência universal
de correções em outros comunicados.

A leitura inicial de três documentos posteriores identificou:

- Vale 0001292814-26-005378: retomada parcial da mina Viga.
- Petrobras 0001292814-26-005346: relatório tributário dos nove meses de 2026,
  em regime de caixa; não substituir o resultado operacional anual por ele.
- Petrobras 0001292814-26-005376: informações financeiras de janeiro a setembro
  de 2026. O escopo trimestral/acumulado não autoriza descartá-lo sem examinar
  eventuais notas de revisão; essa revisão de conteúdo ainda não foi concluída.

Os demais comunicados posteriores e seus anexos não foram examinados integralmente.
Assim, a decisão é **referência anual selecionada e valores corroborados; liberação
pendente**, com razão concreta: avaliação de correções posteriores ainda incompleta.
`unresolved_restatement=null` e `reviews=[]` permanecem no pacote original.
Não existe autorização de uso em produção decorrente desta decisão.

Próximo trabalho: triagem dos comunicados posteriores aos dois anuais, priorizando
correções, demonstrações financeiras e notas de reapresentação, com registro de
quais conteúdos foram efetivamente lidos. Só depois revisar o estado documental
dos candidatos. Nenhum teste com Docker, banco de produção ou provedor de IA foi
necessário nesta etapa documental.

## Triagem dos comunicados posteriores — 24/11/2026

Concluída a coleta dos 193 documentos primários 6-K/6-K/A do inventário, nas datas
dos anuais ou posteriores: 96 Vale (desde 27/03) e 97 Petrobras (desde 09/04).
Arquivos originais e texto extraído estão em
`../official-operating-documents/subsequent-filings/`. O manifesto
`evidencias/subsequent-filings-triage-2026-11-24.json` preserva URL, protocolo,
hash, tamanho do texto, sinais de correção e fila de revisão visual por documento.

Método: pesquisa lexical no texto HTML, seguida de leitura contextual das
ocorrências sinalizadas. Não é leitura integral nem aprovação semântica dos
193 documentos. Os 14 documentos com sinais de correção foram examinados nos
trechos correspondentes, com os seguintes resultados:

| Documentos (nomes no manifesto) | Contexto observado | Alcance da conclusão |
| --- | --- | --- |
| `vale20260710_6ka`, `vale20260623_6k` | Reemissão de materiais de votação de assembleia. | Essas ocorrências não tratam de correção de resultado operacional. |
| `pbr20260408_6ka` | Nota da emenda trata de indicações de conselheiros e votação; ocorrências de restatement tratam de dividendos atualizados pela Selic. | Não são evidência de alteração dos quatro valores. |
| `vale20260721_6ka`, `vale20260721_6k1`, `vale20260416_6k` | Referência de preço 61% Fe e históricos de produção. | Não confundir dados físicos e prêmio de preço com resultado anual. |
| `vale20260331_6k` | Atualização de projeções no Formulário de Referência. | A ocorrência não identifica correção do resultado anual. |
| `vale20260330_6k` | Inversão anterior entre transporte e tributos sobre vendas, declarada sem impacto no total, em relatório de informações selecionadas. | Não atribuir a correção ao total operacional consolidado. |
| `vale20260414_6k`, `pbr20260622_6k` | Índice GRI remete a reapresentações de informações de sustentabilidade. | As páginas remetidas ainda exigem revisão; não classificar o documento inteiro como resolvido. |
| `vale20260428_6k`, `valepr2q26_6k`, `vale20261029_6k` | Streaming, apresentação segmentada, medidas ajustadas, preços e despesas; há referências a períodos anteriores reapresentados. | Reclassificação de apresentação não comprova, por si só, mudança ou manutenção do total anual; permanece necessária conciliação específica. |
| `pbr20260430_6k` | Correção de percentuais geográficos de exportação do 1T25 por conversão de volumes. | Não equivale a correção do resultado operacional anual. |

Não se identificou nesses trechos alteração direta de 26.113/26.876 milhões
(Petrobras) ou 5.897/10.788 milhões (Vale). Essa conclusão é limitada aos trechos
examinados, não uma declaração de inexistência de reapresentação no período.

### Fila visual concreta

Doze documentos têm menos de 1.500 caracteres de texto extraído e imagens
incorporadas, contendo entre 4 e 127 imagens por documento. A heurística identifica
prioridades, não garante que os outros documentos tenham cobertura textual completa.
Nenhum desses doze foi liberado pela ausência de palavras-chave:

- Vale: `vale20260327_6ka`, `vale20260331_6k1`, `vale20260429_6k`,
  `vale20260512_6k1`, `vale20260609_6k1`, `vale20260615_6k1`, `vale20260630_6k`,
  `vale20260710_6k`, `vale20260731_6k`, `vale20261030_6k`.
- Petrobras: `pbr20260422_6k`, `pbr20260428_6k`.

O manifesto contém os URLs completos. A conferência pela web do primeiro arquivo
Vale confirmou que o corpo consiste em imagens. A coleta não encontrou links
HTML/PDF/XML no HTML primário segundo o filtro empregado; isso não substitui a
inspeção dos índices de protocolo e não comprova inexistência de anexos.

Decisão: triagem textual concluída, revisão documental ainda não aprovada.
Próxima ação delimitada: identificar o conteúdo dos doze documentos visuais e
priorizar as páginas financeiras, verificar remissões GRI e conciliar os trechos
de streaming relevantes. O inventário e os downloads já estão preservados;
não refazer a coleta dos 193 arquivos. Os candidatos e o código da aplicação
permanecem inalterados.

## Identificação visual e conciliação — 24/11/2026

As 12 capas foram inspecionadas e seus hashes conferidos. Os títulos estão em
`evidencias/visual-covers-2026-11-24.json`. A cobertura é somente a primeira imagem,
não a leitura integral dos documentos. A última capa recuperada identifica a
apresentação de resultados do 1T26 da Vale.

A fila contém três apresentações trimestrais (1T26, 2T26 e 3T26), materiais de
assembleia e conselho, VBM Day, conferência de mineração, visitas de investidores,
relatório financeiro de sustentabilidade, webinar ESG e suplemento de direitos
humanos. Prioridade seguinte: páginas financeiras das três apresentações
trimestrais; os demais documentos não estão automaticamente liberados.

### Remissões GRI

Na Vale, as ocorrências GRI 2-4 remetidas nas páginas 17, 41, 48, 65 e 66 tratam
nos trechos examinados de emissões, fatores e métodos de cálculo, segurança de
processo e ocupacional, horas trabalhadas e classificação de eventos/fatalidades.
Essas ocorrências específicas não identificam alteração do resultado operacional
anual. Isso não equivale a aprovação integral do relatório.

Na Petrobras, o índice remete à página 5. A página foi lida: descreve escopo,
metodologia, governança e asseguração do relatório e definições de trabalhadores,
mas não enumera as reapresentações. Portanto, a remissão foi verificada, porém
não resolve a revisão: é necessário conferir os indicadores e o ESG Datasheet
referido no próprio relatório. Não inferir ausência de correções a partir dela.

### Streaming: conciliação delimitada

Conferidos o release `vale20261029_6k` e a demonstração `valedfifrs3q26_6k`.
Valores em milhões de USD. Subtraindo do EBIT ajustado o EBITDA de participações,
streaming e os ajustes de impairment/outros ativos não circulantes, obtém-se:

| Período | EBIT ajustado | Participações | Streaming | Ajustes de ativos | Resultado operacional IFRS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3T26 | 2.401 | 328 | 238 | 242 | 1.593 |
| 3T25 | 3.608 | 292 | 155 | 370 | 2.791 |
| 9M26 | 8.151 | 896 | 786 | 346 | 6.123 |
| 9M25 | 8.625 | 786 | 490 | 755 | 6.594 |

As quatro igualdades foram verificadas por cálculo, com resíduo zero. O registro
estruturado é `evidencias/vale-streaming-reconciliation-2026-11-24.json`.
A conciliação distingue as métricas, mas não libera os valores anuais 2025/2024:
seu alcance é trimestral/acumulado, e não resolve toda a revisão de reapresentações.

Estado após esta etapa: candidatos e aplicação inalterados; sem aprovação humana
registrada, sem uso do indicador em produção. Permanecem pendentes a leitura das
páginas financeiras visuais, os anexos/índices ainda não inspecionados e a revisão
das demais notas financeiras posteriores. Não repetir os 193 downloads.

## Apresentações trimestrais da Vale — revisão financeira em 24/11/2026

Concluída a leitura visual das seções financeiras e respectivas notas:

| Documento | Páginas financeiras conferidas | EBITDA proforma (USD milhões) | Streaming em outros ajustes de caixa (USD milhões) |
| --- | --- | ---: | ---: |
| `vale20260429_6k.htm` — 1T26 | 10 a 14 | 3.895 | -257 (p. 13) |
| `vale20260731_6k.htm` — 2T26 | 10 a 15 | 4.066 | -291 (p. 14) |
| `vale20261030_6k.htm` — 3T26 | 10 a 15 | 3.508 | -238 (p. 14) |

Os três valores de EBITDA proforma correspondem aos releases trimestrais
`vale20260428_6k`, `valepr2q26_6k` e `vale20261029_6k`, respectivamente.
A nota do gráfico de EBITDA exclui Brumadinho e itens não recorrentes; os gráficos
incluem contribuições de participações. Não substituir resultado operacional IFRS
por EBITDA proforma. O streaming aparece na passagem de EBITDA para caixa;
esses ajustes de caixa não constituem uma nova medida de resultado anual.

As páginas 12 e 13 do 2T26 atualizam projeções de custos para 2026. A mudança de
projeção é prospectiva; não foi apresentada nesses trechos como reapresentação
do resultado operacional de 2025/2024. As demais páginas financeiras tratam de
custos, fluxo de caixa, hedge e dívida. Não foi identificada nas 17 páginas
financeiras revisadas uma alteração direta dos valores anuais candidatos.
Essa conclusão é limitada à revisão descrita, não a todos os comunicados.

Foram preservadas 46 das 47 imagens esperadas. A página 4 de `vale20260731_6k.htm`
retornou HTTP 504 nas tentativas realizadas e permanece sem inspeção. Ela fica
fora da seção financeira identificada (páginas 10–15), mas não se presume seu
conteúdo. As demais páginas receberam inspeção de visão geral, não revisão
financeira integral. Manifesto com URL, hash, número de página, falha e alcance:
`evidencias/vale-quarterly-slides-2026-11-24.json`.

Verificação: hashes dos 46 arquivos e presença das 17 páginas financeiras
conferidos; conteúdo JSON dos candidatos idêntico ao HEAD. Sem mudança de código,
sem chamada de IA, sem Docker ou banco de produção.

Próximo recorte: revisar nas demonstrações financeiras posteriores as notas de
base de preparação, mudanças contábeis e comparativos de 2025/2024, começando
pela demonstração Vale `valedfifrs3q26_6k.htm`. Manter a página visual faltante e
as remissões/anexos pendentes na fila; não repetir a revisão financeira concluída.

## Notas contábeis Vale 3T26 — 24/11/2026

Revisados a demonstração de resultado comparativa, as notas 3 (segmentos),
4 (custos/despesas) e 30 (base de preparação), e o relatório de revisão independente
em `valedfifrs3q26_6k.htm`. O registro estruturado com URL, hashes e alcance está
em `evidencias/vale-3q26-accounting-review-2026-11-24.json`.

- A nota 30 declara preparação conforme IAS 34 e continuidade das políticas,
  estimativas/julgamentos, gestão de riscos e métodos de mensuração do último
  anual; requer leitura conjunta com o balanço encerrado em dezembro de 2025.
  Isso não significa que nenhum saldo ou estimativa tenha variado no período.
- O resultado compara três e nove meses de 2026/2025. O balanço compara setembro
  de 2026/dezembro de 2025. Não há nesta DRE uma reapresentação da comparação
  anual 2025/2024 que permita aprovar diretamente os dois candidatos anuais.
- A nota 3(a)(i) confirma a separação entre resultados de ativos não circulantes
  e streaming na conciliação do EBITDA. A nota 4 detalha despesas por natureza;
  nos trechos examinados não anuncia correção do resultado operacional anual.
- A busca textual não encontrou termos iniciados por `restat` ou `retrospect`.
  As três ocorrências de `reclass` são da demonstração de resultado abrangente,
  relacionadas à classificação/transferência de ajustes cambiais. Ausência de
  palavra-chave não substitui revisão completa.
- O relatório da PwC, de 29/10/2026, descreve revisão intermediária, de alcance
  menor que auditoria, e menciona opinião sem ressalvas sobre o anual de 2025.
  Não tratar essa menção como revisão humana dos candidatos do projeto.

Conferidas por cálculo oito igualdades em USD milhões: quatro pontes da nota 3
(EBITDA ajustado até lucro antes dos impostos) e quatro da DRE (resultado
operacional mais participações e financeiro até lucro antes dos impostos).
Todas tiveram resíduo zero. Resultados antes dos impostos: 1.534 (3T26),
2.612 (3T25), 5.761 (9M26) e 6.758 (9M25).

Conclusão delimitada: não identificada nessas seções alteração dos valores
operacionais anuais candidatos. Este documento foi revisado no recorte indicado;
não há liberação global de reapresentações nem alteração dos candidatos.
Próximo recorte: notas equivalentes das demonstrações posteriores da Petrobras,
começando pelo documento de janeiro a setembro de 2026, protocolo
`0001292814-26-005376`. Continuam separadas as pendências visuais e de anexos.

## Notas contábeis Petrobras 3T26 — 24/11/2026

Correção da referência de trabalho: o protocolo `0001292814-26-005376`
(`pbr20261123_6k.htm`) é uma apresentação de informações financeiras, não o
conjunto de notas. A revisão foi realizada em `pbrfs3q26usd_6k.htm`, já presente
no acervo. URL, protocolo correto, hashes e cálculos estão em
`evidencias/petrobras-3q26-accounting-review-2026-11-24.json`.

Escopo lido: notas 1 e 2, DRE comparativa, nota 18.4, eventos subsequentes (nota
30), contextos de reclassificação e relatório de revisão independente.
As notas 1/2 informam IAS 34, aprovação em 10/11/2026, manutenção das políticas
e métodos do anual 2025 e ausência de efeito material das novas normas vigentes
em janeiro de 2026. Não se infere daí que todos os saldos permaneçam iguais.

Os resultados comparam três e nove meses de 2026/2025; não reapresentam a DRE
anual 2025/2024. A busca não localizou `restat*` ou `retrospect*`. As ocorrências
de `reclass*` tratam de resultado abrangente/hedge e transferência de dividendos
do patrimônio para o passivo. Isso não constitui prova de inexistência de revisão
em outras partes do acervo.

A nota 18.4 prevê reconhecimento do recebível e dos efeitos no resultado do acordo
de Berbigão/Sururu no 4T26. Não o descreve como correção dos anuais candidatos.
O relatório da KPMG é revisão intermediária; a menção à auditoria anterior não
constitui aprovação documental dos candidatos do projeto.

Verificadas 12 igualdades, três em cada período: lucro bruto mais despesas até
resultado operacional; operacional mais financeiro e participações até resultado
antes dos impostos; resultado antes dos impostos mais tributos até lucro líquido.
Todos os resíduos são zero (USD milhões):

| Período | Resultado operacional | Antes dos impostos | Lucro líquido consolidado |
| --- | ---: | ---: | ---: |
| 9M26 | 33.612 | 34.380 | 24.403 |
| 9M25 | 20.601 | 23.800 | 16.805 |
| 3T26 | 11.511 | 10.987 | 7.747 |
| 3T25 | 7.976 | 8.283 | 6.053 |

Conclusão restrita às seções lidas: nenhuma alteração dos dois valores anuais
candidatos foi identificada. Evidências candidatas e aplicação permanecem
inalteradas, sem liberação do indicador.

Próximo recorte concreto: comparar `pbrfs2q26usd_6k.htm` com sua emenda
`pbrfs2q26usd_6ka.htm`, para identificar exatamente o conteúdo corrigido e seu
possível impacto nos comparativos. Não repetir as revisões direcionadas do 3T26.

## Emenda Petrobras 2T26 — comparação concluída em 25/11/2026

Comparados os arquivos `pbrfs2q26usd_6k.htm` e `pbrfs2q26usd_6ka.htm`.
A nota explicativa informa que a emenda adiciona o Exhibit 101, com dados
interativos, sem alterar as informações do relatório original.

A comparação do texto extraído, removendo cabeçalhos técnicos Inline XBRL e
normalizando espaços, identificou 104 diferenças: 102 inserções e duas remoções,
sem substituições de tokens. Os trechos com números são metadados da emenda e
duas repetições de totais já presentes no original (lucro líquido e resultado
abrangente). As demais diferenças são rótulos/títulos textuais. Não confundir o
aumento do tamanho do texto extraído com alteração dos resultados financeiros.

O resultado antes de financeiro, participações e impostos é igual nas duas versões
(USD milhões): 22.101 em janeiro–junho/2026; 12.625 em janeiro–junho/2025;
14.253 em abril–junho/2026; 5.349 em abril–junho/2025. As quatro comparações foram
verificadas automaticamente. As duas repetições numéricas também foram conferidas
contra os totais existentes no original.

Evidência: `evidencias/petrobras-2q26-amendment-comparison-2026-11-25.json`,
com URLs, hashes, método, posições das diferenças e classificação. Esta análise
compara o conteúdo extraído dos relatórios; não valida os contextos, unidades,
sinais ou taxonomia dos dados eletrônicos.

Decisão: a finalidade declarada da emenda e a comparação não identificam mudança
nos valores operacionais do relatório. Essa pendência específica de comparação
está concluída, sem liberação global dos anuais 2025/2024. Candidatos e aplicação
permanecem inalterados.

Próximo recorte: consolidar a matriz de pendências restantes, separando documentos
já conferidos, notas financeiras ainda relevantes e pendências apenas de cobertura.
Isso deve definir o que efetivamente falta para uma decisão documental, sem repetir
comparações concluídas nem confundir revisão parcial com aprovação dos candidatos.

## Consolidação em 25/11/2026

A fila vigente está em [matriz-pendencias-operacionais.md](matriz-pendencias-operacionais.md).
Ela substitui as indicações históricas de próximo passo acima, preservando os
limites das evidências. Próxima ação: D1, comparação da emenda Vale 2T26.
Nenhuma pendência foi considerada resolvida apenas por sua inclusão na matriz.

## D1 — emenda Vale 2T26, concluída em 25/11/2026

Comparados `valedfifrs2q26_6k.htm` (protocolo 0001292814-26-004012) e
`valedfifrs2q26_6ka.htm` (0001292814-26-004322). A nota explicativa declara
inclusão do Exhibit 101, sem outras alterações às informações do original.

A comparação identificou 92 diferenças de tokens: 85 inserções, uma remoção e
seis substituições. Predominam rótulos/títulos de tabelas e a nota explicativa.
Há cinco trocas de ponto por vírgula: nocionais de derivativos 12.578/9.201
passam a 12,578/9,201 e a quantidade de ações 4.439.159.764 passa a
4,439,159,764. Há também separação de moeda e número (`EUR745` para `EUR 745`).
Esses casos foram examinados no contexto; não são mudanças na linha operacional.
A classificação como apresentação não equivale à validação dos dados XBRL.

Os quatro valores de resultado operacional conferem nas duas versões, em USD
milhões: 2.155 (2T26), 2.004 (2T25), 4.530 (6M26) e 3.803 (6M25).
A verificação automática confirmou as quatro correspondências.

Evidência: `evidencias/vale-2q26-amendment-comparison-2026-11-25.json`.
D1 encerrado no escopo de comparação do relatório; nenhuma alteração dos
candidatos ou aprovação foi criada. Próxima ação: D2 da matriz, notas contábeis
relevantes de 1T26/2T26 das duas empresas, reaproveitando as comparações concluídas.

## D2 — notas do primeiro semestre, concluído em 25/11/2026

Revisão direcionada de `valedfifrs1q26_6k`, `valedfifrs2q26_6k`,
`pbrfs1q26usd_6k` e `pbrfs2q26usd_6k`: base de preparação/políticas,
linhas comparativas de resultado e contextos de reclassificação. Na Vale,
também foi lida a conciliação da nota 3(a). Emendas do 2T26 já comparadas,
sem repetição do trabalho. Não se afirma leitura integral de todas as notas.

Os quatro relatórios declaram manutenção dos critérios do anual de 2025.
Petrobras informa ausência de efeito material das novas normas vigentes em 2026.
A busca textual não encontrou `restat*` ou `retrospect*`; a conclusão considera
o conteúdo das seções lidas, não apenas a ausência desses termos.

As reclassificações observadas tratam de resultado abrangente/hedges e dividendos.
Na Vale 1T26 há ainda a classificação de perda como provável em processo ligado
à Samarco, após decisão judicial de novembro de 2025, com provisão de USD 449
milhões em resultados de participações. O trecho não anuncia correção do resultado
operacional anual. Não confundir mudança de probabilidade de perda com reapresentação.

Verificadas 12 pontes de resultado operacional + financeiro + participações =
resultado antes dos impostos. Também conferidas quatro somas de 1T + 2T = semestre
para o resultado operacional de 2026 e comparativos de 2025, nas duas empresas.
Todos os resíduos foram zero. O resultado semestral é 4.530/3.803 para Vale e
22.101/12.625 para Petrobras (2026/2025, USD milhões).

Evidência: `evidencias/first-half-accounting-review-2026-11-25.json`, com fontes,
hashes, alcance e cálculos. Nenhuma correção dos anuais candidatos foi identificada
nesse recorte. D2 encerrado; não encerra a cobertura global nem cria aprovação.
Próximo item: D3, justificar a escolha do 20-F da Vale frente às inconsistências
texto/imagem do release, sem declarar aquele release integralmente consistente.

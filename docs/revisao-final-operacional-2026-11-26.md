# Pacote para revisão do resultado operacional

Versão: 2026-11-26-1. Estado: aguardando revisão do usuário, que se ofereceu como
responsável. Nenhuma aprovação humana foi registrada. Nenhum valor está liberado
para a aplicação. Este documento encerra a preparação de um recorte de revisão,
não certifica as demonstrações das empresas.

## Quatro observações a conferir

Valores em USD milhões. O snapshot do provedor está em unidades monetárias;
a comparação usa escala 1.000.000 e precisão documental de 1 milhão, com tolerância
máxima de 500 mil USD. As quatro diferenças observadas são zero.

| Ação | Exercício | Valor | Fonte oficial e linha |
| --- | --- | ---: | --- |
| PETR4 | 2025 | 26.113 | 20-F 2025, F-4, resultado antes de financeiro, equivalência e tributos |
| PETR4 | 2024 | 26.876 | Mesmo documento e linha, coluna comparativa 2024 |
| VALE3 | 2025 | 5.897 | 20-F 2025, F-3, Operating income |
| VALE3 | 2024 | 10.788 | Mesmo documento e linha, coluna comparativa 2024 |

Fontes: [Petrobras 20-F](https://www.sec.gov/Archives/edgar/data/1119639/000129281426002168/pbrform20f_2025.htm)
e [Vale 20-F](https://www.sec.gov/Archives/edgar/data/917851/000129281426001844/valeform20f_2025.htm).
O campo do provedor é exclusivamente `annualTotalOperatingIncomeAsReported`.
Não foi usado `OperatingIncome`, EBIT, EBITDA ajustado ou resultado por segmento.

## Alcance e decisões de cobertura

A revisão técnica confrontou as linhas anuais e comparativos, notas selecionadas
de 1T–3T26, emendas financeiras de 2T26 e os conflitos conhecidos do release Vale.
Os registros anteriores preservam páginas, hashes e conciliações. A referência
anual foi escolhida independentemente do release, que permanece inconsistente.

C1: os 13 índices financeiros selecionados foram obtidos. A consulta SEC em
26/11/2026 não encontrou novos protocolos datados a partir de 25/11. O comunicado
Vale de 24/11 acrescentado ontem trata do Vale Day. Os índices identificam os
anexos; eles não equivalem a leitura de todos os contratos, relatórios de reservas,
certificações ou arquivos XBRL. Esses materiais não foram usados como fonte
substitutiva da linha consolidada. Não houve inventário independente exaustivo
de CVM, B3 e todos os canais de RI. Essa é uma limitação explícita do recorte.

C2: além das apresentações trimestrais já examinadas, foram inspecionadas 27
páginas dos nove documentos visuais e quatro páginas adicionais direcionadas.
Os conteúdos, agendas e ressalvas permitiram classificar apresentações de
estratégia/segmento, ESG, direitos humanos e governança. Na proposta de assembleia
Vale, a seção das contas anuais foi examinada diretamente nas páginas 73–74:
resume indicadores em BRL e recomenda aprovação das contas; não substitui a DRE
consolidada em USD. No relatório de sustentabilidade Vale, páginas 5–6 distinguem
a base IFRS de sustentabilidade e sua conexão com as demonstrações financeiras.
Os demais materiais foram excluídos como fontes primárias do indicador, não
declarados integralmente livres de erros. A página 4 de 2T26 já foi recuperada.

C3: a remissão Petrobras foi complementada pelo ESG Datasheet oficial. As notas
examinadas nas páginas 2, 3 e 10 tratam de revisões de emissões, volume de
derramamento de 2024 e vapor vendido em 2021. São métricas distintas da linha
contábil candidata. A divergência tabela/nota no volume de derramamento não foi
apagada nem usada para validar resultado operacional. A leitura não é auditoria
integral do relatório ESG. Referência: [ESG Datasheet oficial](https://sustentabilidade.petrobras.com.br/documents/1449993/0/2025_ESG_DATASHEET_v9_final.pdf/ff4c2eff-8d9c-a6d6-2cf1-933f16d213f1?download=true&t=1784652310000&version=1.0).

Conclusão técnica limitada: no conjunto contábil efetivamente conferido, não foi
identificada reapresentação pendente que altere esses quatro valores. As exclusões
acima não demonstram inexistência de informação fora do recorte. O responsável
deve aceitar expressamente esse alcance ou solicitar ampliação antes de aprovar.

## Decisão solicitada ao responsável

Conferir os valores, linhas, significado contábil, fonte do provedor e alcance
acima. Informar nome para registro e uma decisão: aprovar o pacote inteiro,
aprovar somente observações identificadas, ou solicitar correção/ampliação.
O item 7 de `criterios-resultado-operacional.md` exige revisão identificada;
autorizar desenvolvimento ou oferecer-se como revisor não constitui aprovação.

O arquivo `evidencias/operating-review-package-2026-11-26.json` contém evidências,
hashes dos documentos, digest de cada observação e vínculo ao conteúdo deste
recorte. Qualquer alteração exige novo digest e nova revisão. A avaliação técnica
de reapresentações é registrada como concluída apenas dentro desse alcance;
`reviews` permanece vazio. O validador offline continua sem habilitar runtime.

Após a decisão documental: implementar separadamente a integração e a versão do
contrato, testar interface/MCP/IA com dados locais, revisar e preparar PR. Não há
merge, publicação, acesso ao banco de produção, Docker ou chamada real de IA
autorizados como parte desta conferência documental.

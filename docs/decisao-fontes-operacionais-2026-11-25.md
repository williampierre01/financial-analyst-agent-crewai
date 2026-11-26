# Referências anuais e preparação da integração

## D3 — decisão técnica sobre a fonte

Os quatro candidatos serão confrontados com as demonstrações consolidadas dos
20-F de 2025. Em 25/11/2026, os bytes locais foram novamente comparados aos SHA-256
de `evidencias/annual-source-verification-2026-11-24.json`, e as linhas das tabelas
foram extraídas novamente: Petrobras 26.113/26.876 e Vale 5.897/10.788, USD milhões,
para 2025/2024. As localizações selecionadas são F-4 e F-3, respectivamente.

Na Petrobras, a linha é anterior ao resultado financeiro, à equivalência
patrimonial e aos tributos. Na Vale, é a linha consolidada “Operating income”.
Não se utiliza EBITDA ajustado, resultado de segmento ou o campo normalizado
OperatingIncome do Yahoo como substituto.

As inconsistências texto/imagem identificadas nas versões do release da Vale
permanecem registradas em `vale-release-version-diff.json` e
`vale-release-image-hashes.json`. Dizem respeito às linhas de debêntures, vendas
regionais e EBITDA ajustado de níquel, além de alterações de apresentação e
horizonte de estimativa. A transcrição dos candidatos não depende dessas linhas:
vem diretamente das demonstrações anuais consolidadas identificadas acima.
Isso permite selecionar outra referência sem declarar consistente o release
inteiro ou presumir que nenhuma reapresentação posterior exista.

D3 fica encerrado como escolha técnica de referência, sujeita à revisão
identificada. A avaliação de cobertura C1–C3 continua separada e ainda impede
encerrar a avaliação de reapresentações.

## Pacote preparado, ainda provisório

`evidencias/operating-review-package-2026-11-25-draft.json` preserva as observações
originais, substitui as referências oficiais pelos 20-F selecionados e registra
os quatro digests calculados pela regra 1. O pacote original não foi alterado.
`reviews=[]` e `unresolved_restatement=null` são deliberados. Nenhum valor foi
liberado para a aplicação.

A página 4 da apresentação Vale 2T26 foi recuperada e inspecionada: apresenta
estratégia, negócios e instrumentos organizacionais, sem valores anuais ou
divulgação de reapresentação. Evidência separada em
`evidencias/vale-2q26-page4-review-2026-11-25.json`. Isso fecha apenas essa página,
não a cobertura dos nove outros documentos visuais.

## Sequência de integração após a revisão

1. Concluir e registrar o alcance C1–C3; emitir versão final do pacote. Alterar
   o estado de reapresentações muda o digest e exige recalculá-lo.
2. Solicitar revisão do pacote final, inclusive exclusões e limitações. Registrar
   responsável autorizado, decisão, data com fuso, regra e digests exatos. Não
   preencher uma aprovação em nome do usuário a partir da autorização de trabalho.
3. Introduzir uma fonte de evidências confiável no servidor, separada das entradas
   de usuários e provedores. O resultado offline não basta para habilitar runtime.
4. Versionar o contrato para “Resultado operacional reportado”, sem reaproveitar
   silenciosamente o significado antigo. Exigir correspondência de empresa,
   exercício, moeda, valor e evidência. Ausência ou mudança deve bloquear o campo.
5. Adaptar interface, relatório/MCP e entrada da IA; testar isolamento de anos e
   usuários, revogação por mudança de evidência, fontes alternativas proibidas e
   preservação dos demais dados. Usar fixtures locais; nenhuma chamada real de IA,
   banco de produção ou Docker. Merge e publicação continuam manuais.

Esta sequência prepara a etapa 5; não representa integração implementada ou
aprovada. O bloqueio atual permanece testável independentemente da revisão humana.

## Atualização de cobertura em 25/11

A atualização SEC encontrou um comunicado da Vale de 24/11 que não constava
no inventário anterior: protocolo 0001292814-26-005390. O texto foi lido e trata
do evento Vale Day em 1º/12, sem valores anuais ou correção contábil. A consulta
não acrescentou protocolos da Petrobras ao inventário existente. As evidências
são `sec-cutoff-update-2026-11-25.json` e `vale-new-filing-2026-11-25.json`.

Foram obtidos 12 dos 13 índices financeiros selecionados, incluindo os dois
anuais. O índice Vale 1T26 retornou HTTP 504. A lista de anexos foi preservada em
`financial-filing-indexes-2026-11-25.json`; obter um índice não significa revisar
o conteúdo de cada anexo. Nos quadros anuais de anexos lidos, a Vale distingue
certificações, consentimentos, títulos, subsidiárias, relatórios técnicos de
mineração e dados eletrônicos; a Petrobras distingue instrumentos de dívida,
contratos, subsidiárias, certificações, consentimentos, produção e embarcações.
Essa classificação ajuda a delimitar o recorte, mas não encerra C1.

Validação local: 21 testes em `test_operating*.py` aprovados. Houve um aviso
preexistente de definição incompleta de `lifespan` no carregamento de configurações;
nenhum teste falhou. Não houve acesso ao banco, Docker ou chamadas de IA.

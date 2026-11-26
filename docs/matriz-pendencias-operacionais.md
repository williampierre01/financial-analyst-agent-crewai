> Atualização 26/11/2026 — aprovação recebida: William, responsável neste chat, declarou “revisão final aprovada”. Registro separado em `evidencias/operating-review-approval-2026-11-26.json`, vinculado ao pacote exato e seu alcance. Integração local do contrato 3.1 implementada: campo `reported_operating_income`, referência oficial, correspondência exata e revogação por alteração de evidência/aprovação. Campo normalizado legado permanece nulo. Backend: 163 testes executados, 160 aprovados e 3 ignorados. Interface: testes desktop/mobile passaram; build aprovado. Ainda não publicado nem mesclado. Não editar o documento de revisão aprovado: seu hash faz parte do registro.

> Atualização 26/11/2026: preparação do recorte documental concluída, sujeita à aceitação das limitações pelo revisor. O usuário se ofereceu como responsável; ainda não aprovou valores. Pacote `evidencias/operating-review-package-2026-11-26.json` e documento `revisao-final-operacional-2026-11-26.md` prontos. Os quatro resultados continuam `unverified / missing_matching_review`, sem elegibilidade. 23 testes locais passaram. Próxima ação: revisão identificada do pacote; integração runtime depende dela.

# Matriz de pendências do resultado operacional

Atualizada em 25/11/2026. Este é o ponto de retomada da revisão documental.
O histórico e os limites de cada conferência estão em
[revisao-versoes-operacionais.md](revisao-versoes-operacionais.md).
Não substitui os [critérios de validação](criterios-resultado-operacional.md).

## Estado por observação

Valores em USD milhões, consolidados, exercícios encerrados em 31 de dezembro.

| Observação | Valor candidato | Referência anual selecionada | Situação |
| --- | ---: | --- | --- |
| PETR4 2025 | 26.113 | 20-F 2025, F-4 | Corroborado; sem aprovação |
| PETR4 2024 | 26.876 | Comparativo 20-F 2025, F-4; anual 2024 conferido | Corroborado; sem aprovação |
| VALE3 2025 | 5.897 | 20-F 2025, F-3 | Corroborado; sem aprovação |
| VALE3 2024 | 10.788 | Comparativo 20-F 2025, F-3; demonstração 2024 conferida | Corroborado; sem aprovação |

As referências selecionadas estão em
[evidencias/annual-source-verification-2026-11-24.json](evidencias/annual-source-verification-2026-11-24.json).
O pacote original ainda aponta para documentos anteriores; não foi reescrito.
`unresolved_restatement=null` significa avaliação incompleta, não correção encontrada.
`reviews=[]` permanece vazio. Nenhuma das quatro observações está elegível para análise.

## Trabalho concluído — não repetir

| Conferência | Resultado e limite | Evidência |
| --- | --- | --- |
| Valores anuais e comparativos 2024 | Coincidem nas linhas consolidadas conferidas; não é aprovação | `annual-source-verification-2026-11-24.json` e histórico |
| Inventário SEC até 24/11 | 193 documentos primários posteriores coletados; triagem lexical não é leitura integral | `subsequent-filings-triage-2026-11-24.json` |
| Release Vale 4T25, original e duas emendas | Diferenças identificadas, inclusive inconsistência texto/imagem; não usar release como fonte anual principal | `vale-release-version-diff.json`, `vale-release-image-hashes.json` |
| Capas de 12 documentos visuais | Tipos identificados; capas não liberam conteúdo | `visual-covers-2026-11-24.json` |
| Apresentações Vale 1T26–3T26 | 17 páginas financeiras e notas conferidas; 46/47 imagens obtidas | `vale-quarterly-slides-2026-11-24.json` |
| Streaming Vale 3T26/9M26 e comparativos | Quatro pontes fecharam; diferencia IFRS de medida ajustada | `vale-streaming-reconciliation-2026-11-24.json` |
| Notas selecionadas Vale 3T26 | Oito conciliações fecharam; sem correção anual identificada no recorte | `vale-3q26-accounting-review-2026-11-24.json` |
| Notas selecionadas Petrobras 3T26 | Doze conciliações fecharam; sem correção anual identificada no recorte | `petrobras-3q26-accounting-review-2026-11-24.json` |
| Emenda Petrobras 2T26 | Dados eletrônicos adicionados; quatro valores operacionais iguais; comparação concluída | `petrobras-2q26-amendment-comparison-2026-11-25.json` |

Todos os nomes da última coluna referem-se à pasta `evidencias/`.

## Fila de execução e condições de encerramento

| ID | Prioridade e natureza | Trabalho restante | Critério de encerramento |
| --- | --- | --- | --- |
| D1 | Concluído em 25/11: emenda financeira relevante | Comparar `valedfifrs2q26_6k.htm` e `valedfifrs2q26_6ka.htm`. Comparação concluída: quatro valores operacionais iguais; diferenças de rótulos e separadores registradas em `evidencias/vale-2q26-amendment-comparison-2026-11-25.json`. | Registrar diferenças e se atingem resultado consolidado ou comparativos; divergência material exige resolução. |
| D2 | Concluído em 25/11: revisão financeira complementar | Nas demonstrações USD de 1T26/2T26 das duas empresas, conferir base de preparação, alterações contábeis e notas de comparativos ainda não registradas. Conferência concluída no recorte, com 16 igualdades verificadas; registro em `evidencias/first-half-accounting-review-2026-11-25.json`. | Cada seção relevante recebe referência e conclusão; não usar o 3T26 como prova automática sobre relatórios anteriores. |
| D3 | Concluído como escolha técnica em 25/11 | Referências anuais reconferidas; justificativa e limites em `decisao-fontes-operacionais-2026-11-25.md`. Não encerra C1–C3 nem constitui aprovação. | Vincular os valores ao documento consolidado independente; se não for possível separar o conflito, manter bloqueio. Não declarar o release inteiro consistente. |
| C1 | Cobertura a avaliar | Índices/anexos dos protocolos anuais e financeiros relevantes, demais documentos da triagem e alcance RI/CVM. Inventário atual tem corte em 24/11/2026. | Registrar fonte, intervalo e justificativa de inclusão/exclusão; antes da decisão final, verificar novidades desde o corte. Não afirmar revisão exaustiva de todos os canais. |
| C2 | Lacunas visuais | Página 4 recuperada e examinada em 25/11: estratégia, sem valores anuais. Permanecem nove documentos visuais com apenas capa examinada. | Recuperar ou registrar indisponibilidade; avaliar conteúdo/relevância antes de excluir. A falta dessas páginas não prova mudança financeira. |
| C3 | Remissão de sustentabilidade | Petrobras: página 5 não enumera reapresentações; indicadores/ESG Datasheet ainda não conferidos no ponto necessário. Vale: ocorrências GRI examinadas referem-se a emissões/segurança. | Determinar se a remissão envolve as linhas anuais candidatas. Documentar exclusão motivada se não envolver; não exigir leitura integral de material não pertinente. |
| P1 | Preparação do pacote final | Após D1–D3 e decisão sobre cobertura, preparar nova versão das quatro evidências com os 20-F selecionados, metadados, hashes e regra. | Preservar o snapshot original; indicar alterações e digest de cada evidência. Não reaproveitar aprovação para conteúdo alterado. |
| R1 | Revisão identificada obrigatória | Responsável autorizado revisa o pacote exato, o alcance e as conclusões. | Registro real com responsável, data com fuso, versão da regra, referências e digest; nunca atribuir aprovação fictícia ao usuário. |

D1–D3 são perguntas documentais diretamente ligadas aos valores. C1–C3 são
lacunas de cobertura cuja materialidade precisa ser decidida e registrada;
não são, por si sós, evidência de erro e não devem gerar pesquisa ilimitada.
P1 e R1 dependem das conclusões anteriores. O usuário autorizou as cinco etapas em 25/11. Continuar C1–C3 e finalizar P1; o rascunho versionado já existe em `evidencias/operating-review-package-2026-11-25-draft.json`. Não confundir rascunho com pacote final aprovado.

## Como encerrar esta etapa

A decisão documental deve ser por observação, com fonte exata, critérios 1–7
atendidos e nenhuma divergência relevante sem resolução dentro do alcance
explicitamente revisado. Caso a evidência não sustente uma conclusão, registrar
o motivo específico e conservar o bloqueio, em vez de transformar ausência de
palavra-chave em aprovação. A revisão identificada deve avaliar também as
exclusões e limitações de cobertura.

Mesmo uma validação documental bem-sucedida não libera o campo na aplicação:
o validador offline mantém `eligible_for_analysis=false`. Integração com contrato,
interface/MCP/IA e respectivos testes é uma etapa posterior, separada.

Não iniciar Docker, usar banco de produção ou chamar provedores de IA para esta
fila documental. Merge e publicação continuam manuais.

## Encerramento da preparação em 26/11/2026

C1–C3 receberam decisão de alcance em `revisao-final-operacional-2026-11-26.md`.
Isso encerra a preparação do recorte, não a revisão humana nem uma auditoria
exaustiva. As exclusões e a amostragem estão expostas para aceitação ou ampliação
pelo responsável. Os 13 índices foram obtidos; a remissão ESG foi examinada no
ponto necessário; páginas direcionadas das contas anuais e da base de preparação
Vale foram examinadas. Os registros antigos acima são históricos.

P1: versão 2026-11-26-1 preparada com vínculos aos hashes do alcance e evidências.
Os snapshots e o rascunho anteriores foram preservados. A nova versão registra
avaliação técnica de reapresentações concluída dentro do alcance documentado;
não registra aprovação humana. R1 permanece pendente. O usuário declarou que
fará a revisão, mas oferecer-se como revisor não aprova o pacote.

Testes: 23 aprovados; integridade dos vínculos do pacote e bloqueio por ausência
de revisão verificados. Runtime não alterado; Docker, banco e IA não usados.

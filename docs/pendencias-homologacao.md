# Pendências da homologação no Render

## 15/11/2026 — Gemini concluído nas duas ações

PR #26 Live em `d01ba22`. PETR4 e VALE3 concluíram quatro chamadas cada, todas
com sucesso, usando Gemini `gemini-3.1-flash-lite`. Consumo e durações em
[estado atual](estado-atual.md). Capturas suficientes para encerrar esta rodada
funcional; não repetir chamadas apenas para obter a mesma evidência.

- Qualidade de conteúdo: VALE3 chamou o resultado operacional de "indisponível
  na fonte", embora o sistema o bloqueie por falta de conciliação. Orientações
  compartilhadas por Quant/CIO reforçadas nesta entrega para preservar o motivo
  recebido, sem recuperar o valor. Ainda depende de adesão do modelo; não
  representa reconciliação financeira ou garantia de toda resposta futura.
- Lote futuro de apresentação: eliminar repetição de "publicação original não
  verificada" e padronizar posição do código da moeda nos valores. Adiado.
- Manter separadas a homologação funcional, a revisão de conteúdo e a conferência
  documental. As capturas de novembro não auditam todos os números ou notícias.
- Sem testes/builds locais ou novas consultas reais nesta atualização. CI e
  publicação manual da correção de orientação ainda pendentes.

## Falha de interpretação — 26/10/2026

Logs fornecidos pelo usuário: DeepSeek 402 (saldo insuficiente), seguido de
Groq 413 (8.770 tokens solicitados frente ao limite de 8.000 TPM informado).
Correção em revisão: contexto por etapa, operandos deduplicados sem perda,
mensagens específicas e suspensão de novas tentativas DeepSeek após 402 apenas
na análise atual. Não reiniciar automaticamente a tarefa que falhou.
Detalhes e limites em [limites de IA](limites-ia.md).

Testes desta correção são executados somente no CI. Após merge/deploy manual,
homologar apenas PETR4/VALE3. A otimização não repõe saldo nem garante capacidade
para qualquer resposta/contexto do Groq. Ajustes cosméticos permanecem no lote
futuro; nenhuma cobrança ou mudança de plano foi autorizada nesta etapa.

## Prioridades e lote futuro — 22/10/2026

### Conferência limitada a Vale e Petrobras — atualização

Por solicitação do usuário, limitar a amostra a VALE3 e PETR4 para economizar
tokens; ITUB4 sai desta rodada. Reutilizar capturas, sem gerar novas análises.
Capturas confirmam exibição de PETR4 R$57,36 às13h36 (consulta13h51) e VALE3
R$61,88 às13h47 (consulta14h02), em22/10/2026 Brasília, demonstrativos USD e
bloqueio do P/L entre moedas. Não houve validação independente desses preços.

Conferência documental por amostragem, valores em USD milhões, 2025/2024:

| Empresa | Campo | Aplicativo | Documento da companhia | Resultado |
|---|---|---|---|---|
| Vale | Receita | 38.403 / 38.056 | 38.403 / 38.056 | Coincide |
| Vale | Lucro atribuível aos acionistas | 2.352 / 6.166 | 2.352 / 6.166 | Coincide; app rotula genericamente lucro líquido |
| Vale | Resultado operacional | 11.343 / 11.101 | Operating income 5.897 / 10.788 | Divergência material a reconciliar |
| Petrobras | Receita | 89.195 / 91.416 | 89.195 / 91.416 | Coincide |
| Petrobras | Lucro atribuível aos acionistas | 19.634 / 7.528 | 19.634 / 7.528 | Coincide; app rotula genericamente lucro líquido |
| Petrobras | Resultado operacional | 27.758 / 25.691 | Resultado antes de financeiro, equivalência e impostos 26.113 / 26.876 | Base/definição não reconciliada |

Fontes: [Vale, relatório anual 2025, tabela de resultados p.32](https://www.vale.com/documents/44618/430705/2025_Annual%2BReport%2BEN.pdf/1a40d1ff-c65a-5c46-cc2a-78c4294bd08f?download=false&t=1776265104853&version=1.3)
(trecho indexado consultado; abertura integral limitada pelo tamanho);
[Petrobras, demonstrações 2025 em USD, p.4, cópia publicada no Latibex](https://www.latibex.com/docs/Documentos/esp/resulta/2026/2026.03.06_Consolidated_Financial_Statements_2025_4Q25_USD.pdf).

Prioridade antes de ampliar a análise: reconciliar o conceito/mapeamento de
Operating Income do Yahoo com os demonstrativos. Na Vale, o app afirma aumento
do resultado operacional, mas a linha oficial comparada cai. Não atribuir causa
ou corrigir por número fixo: investigar composição e definição, ou suspender
o uso desse campo enquanto não reconciliado. Distinguir também lucro consolidado
do lucro atribuível aos acionistas na apresentação e na convenção da margem.
FCF, dívida e demais campos não foram integralmente auditados nesta amostra.
Nenhuma correção de código autorizada/realizada nesta conferência.

O usuário solicitou acumular correções de baixo impacto para uma entrega futura.
Este registro não autoriza implementar novas etapas do plano geral.

Evidência mais recente: capturas de PETR4 mostram cotação em BRL com horário,
demonstrativos em USD, aviso de incompatibilidade de moedas, notícia de 2024
separada como contexto histórico e texto mais largo. Isso confirma a exibição
nessa consulta, não a auditoria dos valores ou a homologação de todos os ativos.

### Lote futuro de apresentação (adiado)

- Padronizar percentuais exibidos para duas casas, preservando precisão interna.
- Trocar “P/L não existe” por “P/L não calculado nesta análise” e seu motivo.
- Reduzir repetição e extensão da interpretação e das ressalvas.
- Refinar espaçamento e uso da largura disponível conforme novas capturas.

### Qualidade de conteúdo (prioridade separada)

- Uma notícia sobre Ultrapar apareceu na análise de PETR4, com ressalva explícita
  de falta de relação. Filtrar relevância e duplicidade antes de usar notícias
  na interpretação. Não classificar como mero ajuste visual: se um item alheio
  sustentar uma conclusão financeira, corrigir antes de avançar.

### Próxima sequência proposta

1. Concluir a conferência operacional de VALE3 e ITUB4 no Render: símbolo,
   cotação, horário, moeda, demonstrativos e motivos de indisponibilidade.
2. Conferir uma amostra dos dados frente aos demonstrativos oficiais das empresas,
   incluindo moeda, escala, período e base por ação. Documentar divergências;
   não aplicar câmbio automaticamente apenas para liberar P/L.
3. Antes de convidar outros usuários, concluir testes reais de isolamento de
   análises entre duas contas, acesso negado e revogação de sessão.
4. Com a base conferida, propor a próxima entrega de síntese: achados, mudanças,
   riscos e detalhes de cálculo acessíveis. Metodologia de compra/venda/manter
   permanece dependente de aprovação e validação próprias.

Critério de triagem: apresentação e redação podem aguardar lote; erros de valor,
moeda, identidade do ativo, cálculo, autorização ou conclusão sem suporte não.

Registro: 14/10/2026. Correções adiadas a pedido do usuário.

## Evidências confirmadas

- O painel do Render mostrou o commit 7901396 como publicado.
- As capturas do usuário mostram a interface React exibindo dados de PETR4 antes da interpretação, seguida da resposta da IA.
- O usuário confirmou que o aplicativo solicitou usuário e senha.
- Isso confirma o fluxo observado, não a precisão dos dados ou a fundamentação das conclusões da IA.

## Correções para uma próxima revisão

1. **Layout da interpretação:** tabelas excedem a largura do painel e há rolagem horizontal da página. Conter tabelas no próprio painel e conferir textos longos em desktop e celular.
2. **Idioma e unidades:** a interpretação mistura português e inglês (por exemplo, Diluted EPS e Free Cash Flow) e usa bn BRL, enquanto a interface usa R$ e mi. Padronizar termos, moeda e escala sem alterar valores nem escalar lucro por ação.
3. **Datas de notícias:** o relatório da consulta de 14/10/2026 apresenta itens datados de 15/10/2026. Investigar origem, extração e tratamento de datas; não assumir que sejam inventadas antes da verificação. Exibir data desconhecida quando não houver evidência verificável.
4. **Fundamentação das afirmações:** verificar fontes para comparações com média histórica e explicações causais sobre crescimento do lucro, controle de custos e eficiência operacional. Separar fatos, cálculos e hipóteses; não afirmar causas ou comparações sem base disponível.
5. **Mensagem de progresso:** durante a interpretação, o topo dizia que os dados apareceriam quando disponíveis, embora a tabela já estivesse preenchida. Ajustar a mensagem ao estado real da consulta.

## Ainda não confirmado nesta homologação

- Revisão da exatidão dos números e das fontes citadas pela IA.
- Correção dos pontos listados acima.

Nenhuma correção de código foi realizada neste registro. Não registrar credenciais neste documento.

## Validação operacional — 14/10/2026

- Reinício: Render confirmou sucesso em b725d5b; o usuário confirmou a solicitação de senha em nova sessão anônima e apresentou nova consulta PETR4 com dados e interpretação.
- Rollback: usuário confirmou b839261 como Live, interface carregada e solicitação de senha.
- Restauração: usuário confirmou interface carregada, solicitação de senha e b725d5b novamente como Live.
- O Render informou que o rollback desativaria Auto-Deploy; não houve confirmação posterior de reativação.

O teste de retorno foi entre versões React que diferem em documentação. Não
foi testado retorno ao Gradio, nem uma nova análise completa após rollback ou
restauração. A perda de um identificador específico após reinício não foi
verificada em nuvem. Esses limites não alteram os resultados observados acima.
As correções de layout e conteúdo permanecem adiadas.

## Grupo 1 — layout e responsividade (14/10/2026)

Implementado na branch `codex/layout-responsividade`, a partir de `cef5b49`
(merge confirmado do PR #9), para revisão antes de publicação.

- Demonstrativos e interpretação ocupam a largura disponível em sequência;
  o texto corrido tem limite de largura para leitura no desktop.
- Tabelas Markdown têm rolagem própria e foco por teclado. Blocos de código
  também têm rolagem própria; textos, links e avisos extensos quebram linhas.
- Retirada a contenção por corte do painel, preservando o contorno de foco.
- Testes de regressão usam 12 exercícios, links e palavras extensas, listas,
  citações, código e avisos, entre 320 e 1920 px. Verificam ausência de rolagem
  horizontal da página, posição dos painéis, foco, rolagem por teclado, acesso
  à última coluna e troca para valores integrais.
- Validação: build TypeScript/Vite, 57 testes Python, 20 cenários de interface
  (18 existentes e 2 novos), 3 integrados, formatação e diff sem erros.
  Capturas de desktop e celular emulado revisadas. Chromium emulado não
  substitui teste em aparelho físico/Safari. Dados e IA simulados nos testes.
- Servidores gerenciados separadamente neste ambiente Windows, conforme a
  limitação documentada. Nenhum merge ou deploy realizado nesta etapa.

Os grupos 2 (apresentação), 3 (notícias) e 4 (fundamentação) permanecem pendentes.

## Grupo 2 — apresentação padronizada (14/10/2026)

Base: merge confirmado do PR #10 (`460a492`), branch
`codex/apresentacao-padronizada`.

Investigação: ReactMarkdown já interpreta títulos Markdown válidos. O texto
bruto da consulta originalmente capturada não está disponível, portanto sua
causa específica não foi confirmada. As instruções anteriores enumeravam
os títulos em uma frase, sem regras de quebra de linha, escape ou bloco de
código, nem convenção explícita de moeda/escala. O progresso usava uma frase
fixa e a escondia em telas menores. A formatação determinística das tabelas
já preservava moedas, ausências e valores por ação.

Correções:
- Instruções de saída com títulos em linhas próprias, parágrafos separados,
  indicadores em português, moeda explícita e milhões em `mi`, com exemplo
  de conversão; cotação/EPS sempre sem escala, percentuais e múltiplos sem moeda.
- Exibição reconhece os três títulos conhecidos quando escapados, sem espaço
  após os sinais ou envolvidos em negrito; remove um invólucro Markdown do
  relatório. Não traduz nem converte números por substituição textual.
  Código cercado/indentado, links e valores são preservados.
- Espaçamento consistente de títulos, parágrafos, listas e citações.
- Progresso diferencia coleta pendente, dados disponíveis e coleta sem dados;
  mensagem visível também em celular.

Validação: build, formatação, 57 testes Python, 26 testes de interface e 3
integrados aprovados, com dados simulados. Capturas desktop/celular revisadas.
Os testes cobrem títulos, preservação de conteúdo, moeda desconhecida/estrangeira,
valores negativos/zero/ausentes, milhões e valores por ação, além do progresso.
Foi estabilizada a leitura da última coluna no teste do grupo 1 para aguardar
rolagem por teclado. Servidores gerenciados separadamente no Windows.

Limites: as regras de idioma/moeda da IA são instruções de geração, não garantia
sobre texto livre. Ainda é necessária homologação com consulta real após uma
publicação autorizada. Não houve chamada real a provedores, merge ou deploy.
Grupos 3 (notícias) e 4 (fundamentação) permanecem pendentes.

## Grupo 3 — notícias, datas e fontes (14/10/2026)

Base: merge confirmado do PR #11 (`6c62fbb`), branch
`codex/noticias-datas-fontes`.

### Investigação

`get_market_news` descartava o campo `date` retornado por `ddgs.news` e não
informava o horário da consulta aos agentes. A versão instalada de ddgs pode
normalizar datas extraídas pelos buscadores; esse campo não é evidência de
verificação da página original. Sem o retorno bruto da consulta capturada,
não foi possível determinar a causa específica de 15/10 em consulta de 14/10.
Um dia diferente também pode resultar de fuso, por isso a validação compara
instantes e não apenas a parte de calendário.

### Correções e contrato da ferramenta de notícias

- Envelope registra `query`, `provider=ddgs`, `retrieved_at` em UTC e avisos.
- Cada item conserva título, URL HTTP(S), veículo e resumo da busca; acrescenta
  `date_raw` (texto recebido), `date_origin=ddgs.news.date`, `date_status`,
  `published_at`, `date_label` e `article_verified=false`.
- Apenas ISO com horário/fuso explícito e instante não posterior à consulta
  produz `published_at` normalizado em UTC e rótulo em Brasília. `reported`
  significa informado pela busca, sem confirmação na página original.
- Datas futuras, inválidas, ausentes, relativas ou sem horário/fuso têm
  `published_at=null` e rótulo de publicação não confirmada. Não se inventa
  meia-noite, fuso, data de hoje ou data a partir de URL/título/resumo.
- Resultados sem título ou link válido são descartados com aviso, preservando
  os outros itens. Veículo ausente não é inventado. Erros de busca não expõem
  exceções internas ao agente/cliente.
- Instruções dos agentes exigem título, veículo, URL retornada e `date_label`,
  distinguem consulta de publicação e impedem alegação de leitura integral.

O contrato financeiro/API React não muda. Não há novo provedor nem coleta de
páginas completas. Os metadados seguem no contexto MCP; a reprodução fiel no
texto final depende da adesão do modelo às instruções, ainda não homologada
com consulta real. Datas não confirmadas não são corrigidas automaticamente.

### Validação

Testes sem rede cobrem: 15/10 em fuso que corresponde a 14/10 em Brasília;
data realmente futura; ausência/formato inválido/sem fuso; data antiga;
limite exato da consulta; URLs inválidas; lote parcialmente malformado;
consulta vazia/falha; preservação da origem; serialização e chamada da
ferramenta registrada no MCP. Contrato OpenAPI e `git diff --check` conferidos.
Nenhuma alteração de interface, merge ou publicação no Render nesta etapa.
O grupo 4 (fundamentação) permanece pendente.

Resultado final do grupo 3: 72 testes Python aprovados, incluindo 15 casos de
notícias e a chamada MCP registrada, sem acesso à rede. Suítes de navegador
não repetidas, pois a interface e seu contrato não foram alterados.

## Grupo 4 — fundamentação das afirmações (14/10/2026)

Base: merge confirmado do PR #12 (`655a68e`), branch
`codex/fundamentacao-analise`.

Investigação: a base financeira original estava apenas na tarefa de coleta.
Quant e CIO dependiam do resumo gerado pelos agentes anteriores. As instruções
pediam DCF sem fornecer premissas suficientes, e não definiam limites explícitos
para afirmações sobre média histórica, eficiência, custos ou causalidade.

Correções:
- As três tarefas recebem diretamente a mesma base validada, sem nova coleta,
  preservando referências de indicador, demonstrativo, período, moeda e fonte.
- Regras compartilhadas exigem fatos observados, cálculos e hipóteses distintos;
  referências próximas das afirmações e fórmulas com operandos, resultado e unidade.
- Comparações limitadas aos períodos/campos compatíveis presentes. Dois exercícios
  não autorizam narrativa de média histórica, tendência longa ou comparação setorial.
- Lucro/margem maiores não comprovam eficiência ou controle de custos. Explicações
  de notícias precisam ser atribuídas à fonte e limitadas ao resumo recebido;
  sem evidência, a causa deve permanecer não determinada.
- Hipóteses precisam ser identificadas e dizer que evidência falta. Não são
  obrigatórias nem servem para transformar narrativa plausível em fato.
- DCF deixa de ser uma entrega obrigatória: sem premissas explícitas e rastreáveis,
  deve ser omitido com justificativa, sem inventar WACC, crescimento ou preço-alvo.
- CIO deve confrontar as interpretações anteriores com a base original e omitir
  afirmações sem suporte, mantendo as seções e as regras dos grupos 2 e 3.

Validação: 73 testes Python aprovados; contrato OpenAPI e diff sem erros.
Novo teste da montagem das tarefas verifica a base completa e parcial em cada
etapa (sem alterar o original), preservação dos contextos e callbacks de progresso.
Mocks substituem agentes/modelos: os testes não comprovam adesão de um LLM real.
Não houve alteração de interface/API; suítes de navegador não foram repetidas.

Limites e homologação posterior: estas são instruções de geração e entrega direta
da base, não um verificador semântico ou motor determinístico de cálculos.
Após publicação autorizada, conferir uma consulta real quanto a:
1. Referências de indicador, período, moeda e fonte junto de cada afirmação factual.
2. Fórmulas e operandos que reproduzam os resultados apresentados.
3. Ausência de média histórica/setorial e causalidade sem evidência disponível.
4. DCF omitido quando faltarem premissas, hipóteses identificadas e fontes das
   notícias acompanhadas das ressalvas do grupo 3.
A inclusão da base em cada tarefa aumenta o contexto enviado aos modelos;
latência e consumo não foram medidos em chamadas reais nesta etapa.

Sem consulta real, merge ou deploy no Render. Os quatro grupos têm implementação
em PRs separados; o grupo 4 ainda depende de revisão/merge e a sequência precisa
de homologação integrada após publicação autorizada.

## Nova consulta PETR4 — pendências para correção futura

Evidência: quatro capturas enviadas pelo usuário após os merges dos grupos 1–4.
A tela informa consulta em 14/10/2026 às 22:38, Brasília. O usuário confirmou
Auto-Deploy ativo; as capturas não mostram o SHA publicado no Render.
Registro solicitado pelo usuário, sem iniciar novas correções.

### Observado nas capturas de desktop

- Demonstrativos e interpretação ocupam painéis amplos, sem cortes visíveis;
  títulos principais estão formatados sem sinais `###` expostos.
- Lucro diluído por ação aparece sem escala (`R$ 1,52` em 2025).
- Há fórmulas, distinção entre fatos e cálculos e ressalvas de causa não determinada.
- Notícias visíveis têm título, veículo, URL e ressalva de data informada pela
  busca, não verificada. Isso não comprova as datas nem o conteúdo das publicações.

### Pendências identificadas

1. **Separadores numéricos na interpretação:** a tabela mostra `R$ 19.634,00 mi`,
   enquanto trechos dos cálculos usam `R$ 19,634 mi`. Padronizar a notação
   brasileira sem mudar valores, escala ou unidades por ação. A inconsistência
   é visível; sua origem ainda precisa ser investigada no texto bruto.
2. **Linguagem técnica exposta:** substituir na apresentação termos como
   `income_statement`, `balance_sheet`, `cash_flow`, `period_end`, `as_of`,
   `Diluted EPS` e `driver operacional` por linguagem clara em português,
   preservando a rastreabilidade. Apresentar a fonte de forma compreensível.
3. **Repetição da tabela:** a interpretação enumera quase todos os dados já
   exibidos. Priorizar síntese e cálculos relevantes, mantendo referências
   próximas das afirmações, sem transcrever integralmente os demonstrativos.
4. **Rótulos sem conteúdo:** evitar a repetição de “Hipótese — Nenhuma”.
   Identificar hipóteses apenas quando houver uma hipótese efetiva; manter
   limitações e ressalvas necessárias sem repetição mecânica.
5. **Convenção do ROE:** explicitar que o cálculo mostrado usa patrimônio de
   encerramento, distinguindo-o de patrimônio médio e registrando a limitação.
6. **Markdown ou término do relatório:** na última captura aparece
   `**Petrobras (PETR4), Axia (AXIA3), PetroReconcavo (RECV3) e outros` sem negrito
   renderizado. Inspecionar a continuação e o texto bruto antes de concluir se
   é marcador malformado, resposta interrompida ou apenas limite da captura.
   Conferir a presença integral da seção de limitações e do aviso final.

### Ainda não validado por essas imagens

- Layout e rolagem das tabelas em celular.
- Mensagem de progresso antes e depois da chegada dos dados.
- Alternância entre milhões e valores integrais, preservando valores por ação.
- Abertura dos links e correspondência com as notícias citadas.
- Exatidão dos valores financeiros e das moedas frente à fonte original.
- Relatório completo, incluindo final das notícias, limitações e aviso final.
- Commit efetivamente Live no Render e solicitação de senha em nova sessão.

Não tratar estas capturas como homologação integral nem como confirmação de
precisão financeira. Nenhuma correção, commit, PR ou deploy foi realizado
como parte deste registro; retomar as pendências em trabalho futuro.

## Retomada — clareza dos relatórios (17/10/2026)

O usuário informou sucesso nos novos testes com as três ações sugeridas no
aplicativo. A falha anterior em VALE3 não se repetiu; relação com reinício é
uma hipótese não confirmada. Esses relatos não validam a precisão dos dados.

Implementação local na branch `codex/clareza-relatorios`, base `8b7a0ed`
(main local e remota conferidas antes da edição):

- Cada tarefa recebe referências de apresentação produzidas pelo código, com
  nomes em português, separadores brasileiros, moeda, período e fonte.
  Totais seguem a convenção de milhões; valores por ação permanecem sem escala.
  A base original continua integral e é a referência para calcular, evitando
  usar valores arredondados como operandos. Nenhuma substituição de números
  ou links é feita no texto gerado.
- Regras de síntese priorizam até três achados, preservando ressalvas e fontes;
  proíbem categorias vazias e explicam o ROE sobre patrimônio de encerramento.
  Removida a instrução conflitante de produzir novas tabelas no relatório.
- Respostas sinalizadas pelo provedor como interrompidas por limite de tamanho
  ou filtro não são aceitas como completas, mesmo quando têm texto. O fluxo
  existente tenta Groq após falha do DeepSeek; falha final mantém os dados e
  informa indisponibilidade da interpretação.

Validação: 78 testes Python aprovados com serviços simulados. Cobertura nova
inclui referências para PETR4/VALE3/ITUB4, moeda desconhecida e USD nos dados,
ausências, zero, negativos, milhões, valores por ação, preservação da base,
resposta interrompida, fallback e preservação de chamadas de ferramentas.
O aplicativo continua restrito a códigos da B3; USD no teste é moeda dos
demonstrativos, não suporte novo a ações estrangeiras.

Limites: as referências e regras não garantem adesão do modelo. O sinal de
interrupção do provedor não detecta todo relatório semanticamente incompleto
nem todo Markdown malformado. A causa do trecho da captura continua sem
confirmação, aguardando texto bruto completo. Não houve mudança de interface
ou contrato da API; testes de navegador não foram repetidos. Sem consulta real,
commit, PR, merge ou deploy nesta etapa. Homologação real continua pendente.

## Grupo 1 — indicadores calculados pelo código (17/10/2026)

Após merge do PR #14, o usuário confirmou `730243a` como Live e forneceu
capturas e texto de uma consulta VALE3. A resposta exibe números brasileiros,
ROE sobre encerramento e aviso final, mas ainda repete dados, expõe termos
técnicos e apresenta tabela de notícias extensa. O saldo de 2024 aparece na
tabela, enquanto a interpretação declara ausência de saldo inicial. Datas e
fontes das notícias constam no texto copiado, em colunas fora da área visível.
Isso não verifica os dados frente à fonte nem a causa da falha anterior em VALE3.

Grupo 1 autorizado separadamente; implementação local em
`codex/indicadores-verificados`, a partir de `730243a`:

- Novo módulo calcula ROE sobre encerramento, ROE sobre média simples de dois
  saldos anuais consecutivos, margem líquida, dívida/patrimônio e P/L.
- Resultados incluem fórmula, operandos originais, período, fonte, moeda,
  status e motivo específico de indisponibilidade. Não há nova coleta, câmbio
  ou mutação da base. Cada indicador verifica seus próprios operandos, sem
  depender da presença de fluxo de caixa ou de um único `common_period`.
- Média de saldos exige encerramento no mesmo dia/mês do ano anterior,
  registros únicos, fontes/moedas/unidades compatíveis e saldos positivos.
  Datas fiscais irregulares não são inferidas. A média é uma aproximação e
  não confirma comparabilidade contábil nem representa média ponderada no tempo.
- Denominadores zero/negativos bloqueiam os indicadores; prejuízo no numerador
  do ROE/margem permanece negativo. P/L usa apenas cotação recente datada e o
  último lucro anual disponível, sem apresentá-lo como P/L histórico ou TTM.
- As três tarefas recebem os mesmos cálculos; instruções conflitantes que
  bloqueavam toda análise em base parcial foram ajustadas.

Validação: 87 testes Python aprovados, com serviços simulados; contrato OpenAPI
inalterado e diff sem erros. Testes novos cobrem aritmética, referências dos
dois exercícios, ausência de saldo inicial, duplicidade, período divergente,
moeda/fonte/unidade incompatível, cotação antiga/ausente, denominadores inválidos,
zero/prejuízo, ausência de fluxo de caixa e preservação da base original.

Limites: o módulo verifica os cálculos a partir dos dados recebidos, não a
precisão da fonte. A redação final continua sendo produzida pelo modelo e não
passa por verificação semântica automática; adesão exige homologação real.
Os resultados estruturados são contexto interno, sem alteração da API/UI.
O contexto adicional pode aumentar consumo/latência, não medidos nesta etapa.
Grupo 2 visual não iniciado. Sem commit, PR, merge, deploy ou consulta real.

### Correção após revisão local do grupo 1

A revisão identificou omissão de P/L quando faltava demonstrativo de resultados
e lista vazia quando havia apenas cotação. Correção autorizada pelo usuário:
P/L agora retorna indisponibilidade explícita para demonstrativo ausente ou
ambíguo. Quando faltam resultados e balanço, os cinco indicadores retornam
motivos de indisponibilidade com período nulo, sem inventar datas. Indicadores
sustentados por balanços disponíveis continuam calculados independentemente.

Validação atualizada: 90 testes Python aprovados, contrato OpenAPI inalterado
e diff sem erros. Três regressões novas cobrem ausência de resultados, apenas
cotação e duplicidade do último exercício. Serviços simulados, sem chamada
real a provedores. Alterações continuam locais, sem commit ou publicação.

## Grupo 2 — apresentação das notícias e síntese (17/10/2026)

Base local/remota conferida: `fafc936`, merge do PR #15. Usuário confirmou o
Render operacional e enviou nova consulta VALE3: o relatório agora distingue
ROE médio disponível em 2025 e indisponível em 2024, explica o P/L e chega ao
aviso final. Persistem repetição e `article_verified = false` na apresentação.
As capturas não auditam os dados financeiros ou comprovam o SHA Live.

Investigação dos horários iguais: na biblioteca ddgs instalada, os extratores
de Bing News e Yahoo News convertem datas relativas subtraindo dias do instante
atual, preservando hora/minuto. Isso explica um mecanismo possível para 12:07
em notícias de dias diferentes; sem retorno bruto daquela consulta e identificação
do mecanismo usado, a causa específica continua não confirmada. `news_date`
mantém a informação recebida e a ressalva; nenhum horário foi corrigido por
suposição e nenhuma página original foi consultada.

Implementação local em `codex/apresentacao-noticias`:
- Transformação de apresentação sobre a estrutura Markdown, limitada à seção
  de notícias. Tabelas com colunas de título e URL reconhecidas viram listas;
  o título recebe o link quando isso não elimina conteúdo adicional. Fonte,
  data, ressalvas e colunas extras são preservadas. Tabelas desconhecidas ficam
  intactas. Números, datas, destinos de links e texto financeiro não são reescritos.
- URLs usadas como rótulo de links nas notícias recebem rótulo curto com domínio.
  Campos reconhecidos da tabela e alguns termos técnicos em prosa recebem
  apresentação portuguesa. Código e títulos descritivos de links são preservados.
  Isto não é um tradutor genérico nem um verificador de fatos.
- Células com links permitem quebra de linha; tabelas numéricas preservam a
  rolagem existente. Testes anteriores de tabelas extensas continuam aplicáveis.
- Orientações pedem até três parágrafos temáticos com achados, fórmulas e
  referências, sem inventário inicial, com ressalvas gerais concentradas no final.
  Notícias em lista com título clicável e explicação sobre normalização de datas.
  A concisão do texto novo ainda depende da adesão do modelo; nenhum trecho
  factual é removido automaticamente para encurtar a resposta.

Sem mudança no contrato da API, cálculo financeiro ou coleta de notícias.
Sem consulta real, commit, PR, merge ou publicação nesta etapa.

Validação do grupo 2: 90 testes Python e 34 testes de interface aprovados;
build TypeScript/Vite, formatação, contrato OpenAPI e diff conferidos.
Capturas desktop/celular emulado revisadas. A suíte cobre conversão de tabela
de notícias, preservação de campos adicionais, URLs, datas, valores e código,
links por teclado, tabelas desconhecidas, textos extensos e larguras de 320
a 1920 px. Dados e IA simulados; navegador Chromium não substitui aparelho
físico/Safari. Testes integrados de servidor não repetidos: contrato inalterado.
Não foi reproduzida rolagem horizontal da página nos cenários testados; isso
não comprova a causa da barra vista anteriormente na sessão do usuário.

### Revisão do grupo 2 — preservação de conteúdo

Correções autorizadas após revisão: removidas substituições de termos técnicos
em prosa livre, pois poderiam alterar títulos e citações. Tradução automática
restrita aos campos de tabelas reconhecidas. A conversão de true/false no campo
de verificação agora exige uma única célula textual simples; links, código e
formatação são preservados, sem descarte de destinos ou estrutura.

Acrescentados casos de regressão para títulos/citações e células de verificação
com links, negrito e código. As expectativas anteriores foram ajustadas para
preservar também prosa técnica literal. Campos técnicos em texto livre podem
continuar visíveis; as instruções de geração orientam a redação em português.

Por solicitação do usuário, não foram executados novos testes locais nem aberto
o aplicativo nesta revisão. Os resultados de 90 testes Python e 34 de interface
acima pertencem à versão anterior a estas correções. Os testes novos/ajustados
aguardam execução no CI; avaliação visual será feita no Render após publicação
manual autorizada. Apenas formatação dos arquivos e revisão do diff realizadas.


## 28/10/2026 — Provedores configuráveis e consumo por análise

- Entrega em revisão: seleção DeepSeek/Groq, alternativa opcional, medição por
  tentativa e limites explícitos; Gemini fica no próximo PR.
- CI: novos contratos offline para ordem, chave necessária, limites, fallback,
  tokens ausentes/resposta cortada e isolamento de medidores. Sem execução local.
- Após merge/deploy: conferir PETR4 e VALE3 e salvar os resumos `llm_analysis`
  para levantar consumo real. Aproximadamente quatro chamadas é estimativa,
  não resultado observado em produção.
- Conferir logs visíveis no Render e ID correspondente à análise da API.
- Modelos e cotas Google/benefício estudantil ainda não verificados na conta.
- Sem alteração de plano, recarga ou nova configuração de produção nesta etapa.
- Ajustes cosméticos continuam acumulados nas pendências anteriores.

## 07/11/2026 — Medição confirmada e integração Gemini

PR #25 incorporado e Render Live confirmado pelo usuário. PETR4 e VALE3 tiveram
4 chamadas lógicas e 5 tentativas cada: DeepSeek sem saldo, três sucessos Groq
e falha 429 no CIO. Consumo conhecido: PETR4 6.505 entrada/2.801 saída;
VALE3 5.712 entrada/2.696 saída. Totais parciais, não custo de análise completa.
IDs e durações registrados em `estado-atual.md`.

Gemini preparado em PR separado, com modelo explícito, ferramentas e medição.
Homologação pendente: CI, merge/deploy pelo usuário, chave/modelo/cota no Google
AI Studio e duas análises completas (PETR4/VALE3). Sem mudança de plano ou cobrança.
Correções cosméticas continuam acumuladas; indisponibilidade da interpretação
permanece prioridade funcional.

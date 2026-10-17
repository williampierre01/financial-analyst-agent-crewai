# Pendências da homologação no Render

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

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

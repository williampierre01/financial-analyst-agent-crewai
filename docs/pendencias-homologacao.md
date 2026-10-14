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

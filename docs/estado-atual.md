# Estado atual do projeto

Atualizado em **15/11/2026**. Código entregue, publicação e homologação são
registrados separadamente.

## Base incorporada e publicada

- React + FastAPI no Render; dados financeiros preservados quando a IA falha.
- Firebase, autorização por UID e sessões no Neon; MFA administrativo.
  Entrada, saída e nova entrada confirmadas pelo usuário. Conferência completa
  de isolamento entre usuários ainda pendente.
- Yahoo Finance; moedas e datas preservadas. Cotação BRL e demonstrativos USD
  não são combinados sem conversão validada. Resultado operacional não conciliado
  permanece indisponível. Indicadores calculados pelo código.
- PR #25 incorporado em 07/11/2026, commit `9f535e9`, e Render confirmado Live
  nas capturas do usuário. CI aprovado: backend Linux/Windows, PostgreSQL e
  interface/contratos. Sem testes ou builds locais.
- Seleção DeepSeek/Groq, alternativa opcional, limites de tentativas e medição
  por análise publicados. Sem repetições ocultas do SDK.

## Histórico de falhas — 07/11/2026

Evidências: capturas dos logs do Render fornecidas pelo usuário em 07/11/2026.

| Análise | Chamadas lógicas | Tentativas | Entrada reportada | Saída reportada | Duração total |
|---|---:|---:|---:|---:|---:|
| PETR4 | 4 | 5 | 6.505 | 2.801 | 32,82 s |
| VALE3 | 4 | 5 | 5.712 | 2.696 | 27,98 s |

- PETR4: `4b04f4e0-5c44-4d92-9325-eaf31b4c35b3`, aproximadamente 04:23–04:24 (Brasília).
- VALE3: `2835fd84-062a-4fc0-97cc-5e2977cb0a56`, aproximadamente 04:30–04:31 (Brasília).
- Em ambas: DeepSeek fez uma tentativa sem sucesso por falta de saldo; Groq
  fez quatro, com três sucessos e HTTP 429 na quarta, etapa CIO.
- Os tokens cobrem **somente três respostas com uso informado**. Não representam
  consumo completo, custo de uma análise bem-sucedida nem garantia de gratuidade.
- O 429 mostrado não identifica qual cota foi atingida. Não atribuir a TPM,
  limite diário ou tempo de reset sem evidência adicional.
- Dados financeiros permaneceram visíveis; interpretação indisponível.
  Portanto, medição e tratamento de falhas estão observados, mas a interpretação
  completa desta versão ainda não foi homologada.

## Gemini publicado e homologado funcionalmente — 15/11/2026

PR #26 incorporado em `d01ba22`; captura do Render confirma Live em
15/11/2026, 15:39 (Brasília), após configuração pelo usuário. CI do PR aprovado
(backend Linux/Windows, PostgreSQL e interface). Sem execução local.

- Gemini selecionável como principal ou alternativa, pelo endpoint oficial
  compatível com Chat Completions, usando o SDK já instalado.
- `GEMINI_MODEL` e `GEMINI_API_KEY` obrigatórios somente se selecionado.
  Não presumir modelo disponível ou cota gratuita na conta do usuário.
- Preservação das assinaturas opacas das chamadas de ferramentas apesar da
  reconstrução das mensagens pelo CrewAI; armazenamento apenas por análise.
- Histórico de ferramentas de outro provedor não é enviado ao Gemini com
  assinaturas inventadas. Nesse caso, a tentativa é recusada localmente e
  a próxima alternativa configurada pode ser usada.
- Limites e telemetria existentes mantidos. Nenhuma mudança financeira ou visual.
- Contratos offline preparados para CI: serialização real do SDK com HTTP
  simulado, ferramentas sequenciais/paralelas, isolamento, fallback, limites,
  respostas cortadas e contadores ausentes. Não executados localmente.

Configuração observada nos logs: `gemini`, modelo `gemini-3.1-flash-lite`.
As duas análises completaram o relatório, com quatro sucessos e nenhuma falha
cada; não houve tentativa de outro provedor nessas execuções.

| Análise | Chamadas lógicas | Tentativas | Entrada reportada | Saída reportada | Duração total |
|---|---:|---:|---:|---:|---:|
| PETR4 | 4 | 4 | 13.856 | 3.623 | 82,709 s |
| VALE3 | 4 | 4 | 13.911 | 3.561 | 52,882 s |

Evidência: capturas do usuário, resumos `llm_analysis` às 17:34:47 e 17:38:06
(Brasília), respectivamente. Uso informado nas quatro respostas de cada análise;
não é medição de cobrança, nem garantia de cota ou consumo futuro. Os totais
parciais de 07/11 não são comparáveis diretamente a estas análises completas.

Capturas dos relatórios confirmam moedas separadas, bloqueio do P/L BRL/USD,
ROE sobre encerramento explicitado e notícias históricas separadas. Conferência
de coerência da apresentação; não constitui auditoria dos demonstrativos ou
verificação dos artigos originais. Teste restrito a PETR4 e VALE3, sem novas
consultas para repetir evidência já disponível.

## Próxima entrega e pendências

- Nesta branch: reforço das orientações para preservar o motivo do bloqueio do
  resultado operacional. Falta de conciliação não significa ausência na fonte.
  A orientação não é um verificador semântico e depende da adesão do modelo.
  Correção ainda não publicada; CI e merge/deploy manual pendentes.
- Reconciliar definição do resultado operacional antes de voltar a utilizá-lo.
- Antes de convidar outros usuários, validar isolamento entre duas contas,
  acesso negado e revogação de sessão.
- Ajustes pequenos permanecem no [backlog](pendencias-homologacao.md).
- Benefício estudantil para API não confirmado; nenhuma recarga ou ativação
  de cobrança realizada por esta entrega. Nenhuma credencial registrada.

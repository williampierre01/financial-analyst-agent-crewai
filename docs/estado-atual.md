# Estado atual do projeto

Atualizado em **07/11/2026**. Código entregue, publicação e homologação são
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

## Medições reais — PETR4 e VALE3

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

## Entrega em preparação — Gemini

Branch `codex/integracao-gemini`, ainda não publicada:

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

## Próximos passos de homologação

1. CI e revisão do PR; merge/deploy manuais pelo usuário.
2. Conferir modelo com ferramentas e cota disponível no projeto do Google AI
   Studio. O benefício da assinatura estudantil para API continua não verificado.
3. Configurar Gemini inicialmente sozinho, conforme [guia](provedores-ia.md),
   para medir seu comportamento sem misturar provedores.
4. Testar somente PETR4 e VALE3; conferir relatório completo, moedas, fontes,
   chamadas e tokens nos resumos `llm_analysis`.

Nenhuma chave Google, chamada real ao Gemini, mudança no Render, recarga ou
ativação de cobrança foi realizada nesta entrega. Ajustes pequenos permanecem
no [backlog](pendencias-homologacao.md).

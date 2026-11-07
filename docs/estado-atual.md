# Estado atual do projeto

Atualizado em **28/10/2026**. Este documento distingue código entregue,
publicação e homologação; não substitui o plano geral nem o backlog.

## Base incorporada

- React + FastAPI no Render; dados financeiros antecipados e interpretação
  separada. Uma falha de IA não remove os demonstrativos.
- Autenticação Firebase, autorização por UID e sessões no Neon; MFA TOTP
  administrativo. O usuário confirmou entrada, saída e nova entrada.
  A conferência completa de isolamento entre usuários continua pendente.
- Yahoo Finance como fonte financeira. Moeda e data preservadas; cotação BRL
  e demonstrativos USD não são combinados sem conversão validada.
- Indicadores calculados pelo código. Resultado operacional não conciliado
  permanece indisponível, com aviso. Sem metodologia aprovada para emitir posição.
- PR #24 incorporado em 26/10: contexto reduzido sem descarte de dados e
  diagnóstico de falta de saldo/capacidade. CI passou naquele PR. O merge foi
  confirmado no GitHub; a publicação e homologação desse commit não foram
  confirmadas nesta revisão.

## Entrega atual: provedores configuráveis e medição

Implementação na branch `codex/provedores-configuraveis`, ainda não publicada:

- Principal e alternativa configuráveis entre DeepSeek e Groq; alternativa
  pode ser desativada. Somente as chaves dos provedores selecionados são exigidas.
- Modelos e limites de saída configuráveis, mantendo os padrões anteriores.
- Limites por análise: tentativas, tamanho de solicitação e timeout por pedido.
  Sem repetições ocultas do SDK. Credenciais inválidas/saldo insuficiente
  suspendem aquele provedor até a próxima análise.
- Logs de cada tentativa e resumo por análise: ID, etapa, provedor, modelo,
  duração, resultado e tokens reportados. Sem prompts, respostas ou credenciais.
- ID correlacionado ao trabalho da API; análises concorrentes têm medidores
  separados. Sem alteração no contrato público ou na tela do usuário.

**Validação:** testes offline preparados para CI; execução e resultado serão
registrados no PR. Não foram executados testes, builds ou aplicação localmente.
Nenhuma chamada real a provedores, recarga ou mudança de plano nesta entrega.

## Quantas chamadas fazemos

Fluxo esperado: duas interações de notícias (pedir ferramenta e ler resultado),
uma quantitativa e uma de interpretação: aproximadamente **4 chamadas lógicas**.
Não é uma contagem medida em produção nem uma garantia: o ciclo de ferramentas
e falhas podem aumentá-la. Com um 402 inicial e quatro respostas da alternativa,
são cinco tentativas. Sem dados financeiros aceitos, são zero chamadas de IA.

O próximo deploy permitirá conferir a contagem real em `llm_analysis`. Tokens
ausentes não significam consumo zero. Totais conhecidos não são uma fatura;
não se estima preço nem se presume gratuidade a partir do nome do modelo.

## Próxima entrega: Gemini

1. Integrar um adaptador compatível com ferramentas e respostas completas.
2. Conferir modelos e cotas efetivamente disponíveis no projeto Google.
3. Verificar elegibilidade do benefício estudantil para créditos de API:
   assinatura Gemini não significa API ilimitada; benefício ainda não confirmado.
4. Homologar **somente PETR4 e VALE3**, comparando a mesma base financeira e
   registrando chamadas, tokens, falhas e qualidade de interpretação.

Gemini ainda não é selecionável nesta entrega. A segunda integração será um PR
separado após a validação desta base. Não ativar cobrança ou comprar créditos
sem autorização específica. Trocar modelos exige compatibilidade com ferramentas;
uma configuração válida não garante disponibilidade ou saldo no provedor.

## Forma de trabalho acordada

- Testes e builds no CI; homologação no Render pelo usuário.
- Merge e deploy manuais pelo usuário, sem alteração automática do ambiente.
- Correções pequenas acumuladas no [backlog](pendencias-homologacao.md).
- Referências: [configuração e medição de IA](provedores-ia.md),
  [limites de IA](limites-ia.md) e [plano geral](plano-geral-desenvolvimento.md).

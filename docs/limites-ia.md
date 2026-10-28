# Limites e falhas dos serviços de IA

Diagnóstico de 26/10/2026 pelos logs do Render: DeepSeek respondeu HTTP 402
(`Insufficient Balance`). O fallback Groq respondeu 413: solicitação de 8.770
tokens diante de um limite de 8.000 TPM informado para aquela conta/modelo.
São falhas diferentes, não uma falha de login nem da coleta financeira.

## O que cada limite significa

- **Saldo**: créditos da API pagam entrada e saída. HTTP 402 exige resolver
  o saldo na conta DeepSeek; esperar ou diminuir texto não repõe créditos.
- **Contexto**: tamanho que o modelo aceita em uma interação, independente
  do saldo e dos limites de uso da conta.
- **Saída**: este app solicita no máximo 8.000 tokens no DeepSeek e 2.500 no
  Groq, incluindo o orçamento que o provedor aplica ao raciocínio. Não são
  tokens gratuitos. Uma resposta cortada não é publicada como completa.
- **Ritmo/capacidade**: TPM é tokens por minuto, não uma franquia mensal;
  concorrência conta solicitações simultâneas. A conta e o modelo definem
  os limites efetivos. Uma análise pode envolver várias chamadas e ferramentas.

Segundo a [tabela oficial consultada em 26/10/2026](https://api-docs.deepseek.com/quick_start/pricing/),
o alias usado pelo app, `deepseek-v4-flash`, é atendido pelo atual `deepseek-flash`:
contexto de 1 milhão e saída máxima de 384 mil tokens (o app usa teto menor).
Por milhão de tokens, entrada sem cache custa US$ 0,15 fora do pico / US$ 0,30
no pico; saída US$ 0,60 / US$ 1,20. Entrada com cache tem outra tarifa.
Saldo concedido e recarregado podem ser consumidos; não há promessa de uma
franquia gratuita permanente neste app. Consulte a tabela antes de recarregar.
O [limite de concorrência](https://api-docs.deepseek.com/quick_start/rate_limit/)
é por conta, não por chave. Os [códigos de erro](https://api-docs.deepseek.com/quick_start/error_codes/)
distinguem falta de saldo, credenciais, ritmo e indisponibilidade.

## Correção implementada

- Coleta de notícias não recebe cópias dos demonstrativos nem métricas.
- Quant recebe a base original e indicadores, sem texto de notícias ou regras
  editoriais finais. CIO recebe a base, métricas, notícias e síntese quantitativa.
- Operandos repetidos têm uma tabela de referências sem perda de valores,
  datas, moedas, fontes, nulos, fórmulas ou motivos de indisponibilidade.
- JSON compacto e horários de apresentação sem uma segunda cópia dos valores.
- Um 402 suspende DeepSeek apenas na instância da análise atual. O fallback
  continua disponível; a próxima análise volta a tentar DeepSeek.
- Falha de agente não reinicia a mesma tarefa automaticamente. Na camada configurável de 28/10, as tentativas
  internas do SDK ficam desativadas para tornar a contagem verificável. Veja
  [configuração e medição](provedores-ia.md).
- Logs do app identificam provedor/categoria sem imprimir o corpo do erro;
  saída verbosa dos agentes desativada. A interface preserva os dados financeiros.

Não se corta o histórico de ferramentas nem se descartam dados para caber
num orçamento estimado. A redução não garante que qualquer análise caiba no
Groq: contexto dinâmico, resposta e uso recente da conta ainda podem atingir
limites. Não houve recarga, alteração de plano ou chamada paga nesta correção.
Validação automatizada no CI; homologação real restrita a PETR4 e VALE3 após
merge/deploy manual do usuário.

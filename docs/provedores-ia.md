# Configuração e medição dos provedores de IA

A configuração pertence ao servidor. Nenhuma chave é enviada ao navegador.
Os padrões preservam DeepSeek seguido de Groq; não é necessário alterar o
ambiente para manter esse fluxo. Gemini será integrado separadamente.

| Variável | Padrão | Valores/limites |
|---|---|---|
| `LLM_PRIMARY_PROVIDER` | `deepseek` | `deepseek` ou `groq` |
| `LLM_FALLBACK_PROVIDER` | `groq` | outro provedor, `none` ou vazio |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | modelo compatível com o adaptador |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | modelo compatível com ferramentas |
| `DEEPSEEK_MAX_OUTPUT_TOKENS` | `8000` | 1–16000 |
| `GROQ_MAX_OUTPUT_TOKENS` | `2500` | 1–16000 |
| `LLM_MAX_ATTEMPTS` | `12` | 1–30 por análise, incluindo falhas e fallback |
| `LLM_MAX_REQUEST_CHARS` | `60000` | 1–200000, mensagens + ferramentas serializadas |
| `LLM_TIMEOUT_SECONDS` | `60` | 1–120 por operação de rede do SDK |

Exemplo para usar apenas Groq: `LLM_PRIMARY_PROVIDER=groq` e
`LLM_FALLBACK_PROVIDER=none`, com `GROQ_API_KEY` configurada. Para inverter:
principal `groq`, alternativa `deepseek`, com ambas as chaves. Provedores
repetidos, nomes desconhecidos, chave ausente ou limites inválidos impedem a
interpretação com mensagem pública, preservando os dados financeiros.

Endpoints e nomes das variáveis de credenciais são fixados pelo adaptador.
Um identificador de modelo sintaticamente válido não comprova suporte a
ferramentas, parâmetros, acesso da conta ou gratuidade. DeepSeek mantém
`thinking: enabled`; a troca para famílias incompatíveis exige outro adaptador.
Não há detecção automática de preço nem teto monetário. Um provedor configurado
pode consumir saldo já existente. Para impedir uso de um provedor, remova-o
da seleção, não apenas altere o modelo.

## Tentativas e preservação de dados

Cada chamada lógica percorre a lista configurada, uma vez por provedor. SDK
com `max_retries=0`; agentes com `max_retry_limit=0`. Após 402/401/403, aquele
provedor não é tentado novamente na mesma análise. Outros erros podem voltar
a ser tentados na próxima chamada lógica, dentro do teto de tentativas.

O teto de caracteres é preventivo, **não é conversão para tokens** nem garantia
de caber no TPM/contexto do provedor. Solicitações maiores são recusadas sem
truncar demonstrativos ou histórico de ferramentas. Não há repetição automática
para reduzir o texto. Uma resposta incompleta também não é publicada como completa.
O timeout de rede não substitui o limite global do trabalho da API.

## Como conferir no Render

Pesquisar `llm_analysis` para o resumo final ou `llm_attempt` para as tentativas.
O campo `analysis_id` corresponde ao ID retornado pela API; no uso direto sem
API, um ID é gerado. A etapa identifica notícias (`gathering`), Quant ou CIO.

- `logical_calls`: entradas no adaptador, incluindo recusas locais.
- `attempts`: invocações do SDK; inclui falhas antes de uma resposta HTTP.
- `successes`/`failures`: resposta utilizável ou falha, por provedor/modelo.
- `usage_reported`: respostas com ambos os contadores de tokens presentes.
- `input_tokens_reported` e `output_tokens_reported`: soma do que foi informado,
  inclusive respostas cortadas. Não incluem estimativa de falhas sem `usage`.
- `duration_ms`: duração da tentativa; no resumo, duração total da análise,
  incluindo coleta e ferramentas.

Os tokens de entrada/saída seguem os campos fornecidos pela API; raciocínio e
cache não são separados nesta etapa. Se `usage_reported < attempts`, a soma
de tokens é parcial. Falha sem contador não prova que nada foi cobrado.
Sem dados financeiros, o resumo registra zero chamadas.

Registros ficam nos logs do serviço, sem persistência adicional no Neon.
Se o processo for encerrado abruptamente, pode faltar o resumo final; tentativas
já concluídas continuam identificáveis nos logs. Homologação manual restrita
a PETR4 e VALE3, após CI, merge e deploy pelo usuário.

# Configuração e medição dos provedores de IA

A configuração pertence ao servidor. Nenhuma chave é enviada ao navegador.
Os padrões preservam DeepSeek seguido de Groq; não é necessário alterar o
ambiente para manter esse fluxo. Gemini é uma opção explícita; não é ativado
automaticamente ao publicar o código.

| Variável | Padrão | Valores/limites |
|---|---|---|
| `LLM_PRIMARY_PROVIDER` | `deepseek` | `deepseek`, `groq` ou `gemini` |
| `LLM_FALLBACK_PROVIDER` | `groq` | outro provedor, `none` ou vazio |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | modelo compatível com o adaptador |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | modelo compatível com ferramentas |
| `GEMINI_MODEL` | sem padrão | obrigatório se Gemini selecionado; conferir disponibilidade na conta |
| `DEEPSEEK_MAX_OUTPUT_TOKENS` | `8000` | 1–16000 |
| `GROQ_MAX_OUTPUT_TOKENS` | `2500` | 1–16000 |
| `GEMINI_MAX_OUTPUT_TOKENS` | `8000` | 1–16000; teto da aplicação, não cota gratuita |
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

Cada chamada lógica percorre a lista configurada. Em HTTP 503 há no máximo
uma tentativa extra por análise inteira, no mesmo provedor, após 2 segundos.
Ela conta em `LLM_MAX_ATTEMPTS`, mantém a mesma chamada lógica e gera outro
`llm_attempt`; `llm_retry` registra a espera e o identificador da análise.
Não há essa repetição para outros erros, inclusive 401/402/403/413/429.
Sem orçamento ou tempo para a espera, não há repetição. Depois da segunda
falha, segue a alternativa configurada, se houver. SDK
com `max_retries=0`; agentes com `max_retry_limit=0`. Após 402/401/403, aquele
provedor não é tentado novamente na mesma análise. Outros erros podem voltar
a ser tentados na próxima chamada lógica, dentro do teto de tentativas.

O teto de caracteres é preventivo, **não é conversão para tokens** nem garantia
de caber no TPM/contexto do provedor. Solicitações maiores são recusadas sem
truncar demonstrativos ou histórico de ferramentas. Não há repetição automática
para reduzir o texto. Uma resposta incompleta também não é publicada como completa.
O timeout de rede não substitui o limite global do trabalho da API.
O prazo global é compartilhado com o LLM: novas tentativas são bloqueadas
após seu vencimento e o timeout da requisição é limitado ao tempo restante.
Isso não cancela à força threads ou ferramentas já em execução; o timer da
API continua preservando os dados recebidos e impedindo atualizações tardias.

## Como conferir no Render

Pesquisar `llm_analysis` para o resumo final ou `llm_attempt` para as tentativas.
O campo `analysis_id` corresponde ao ID retornado pela API; no uso direto sem
API, um ID é gerado. A etapa identifica notícias (`gathering`), Quant ou CIO.

- `logical_calls`: entradas no adaptador, incluindo recusas locais.
- `attempts`: tentativas por provedor; inclui recusas locais do histórico e
  falhas antes de uma resposta HTTP. Não é necessariamente número de pedidos cobrados.
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

## Ativação manual do Gemini

No Render, após merge/deploy, configurar:

```text
LLM_PRIMARY_PROVIDER=gemini
LLM_FALLBACK_PROVIDER=none
GEMINI_MODEL=<identificador disponível no seu projeto Google AI Studio>
GEMINI_API_KEY=<chave do mesmo projeto, apenas no servidor>
GEMINI_MAX_OUTPUT_TOKENS=8000
```

Substituir os dois valores entre `<...>`; não colar os marcadores literalmente
nem enviar a chave no chat. Escolher um modelo de texto que aceite ferramentas
e `reasoning_effort=low`. O adaptador envia esse nível para limitar raciocínio;
isso não garante quantidade de tokens ou sucesso dentro do teto de saída.
Endpoint fixo: `https://generativelanguage.googleapis.com/v1beta/openai/`.
Sem nova dependência, pesquisa Google embutida ou mudança na coleta de notícias.

Começar sem alternativa permite medir Gemini isoladamente. Depois, `groq` ou
`deepseek` podem ser selecionados como alternativa com a respectiva chave.
Não há espera/repetição automática após 429, nem rotação de chaves ou projetos.
Não ativar cobrança ou comprar créditos sem autorização. Assinatura Gemini Pro
estudantil não comprova cota de API; verificar projeto, modelo e benefício na conta.

O CrewAI reconstrói mensagens de ferramentas. O adaptador guarda a resposta
original do Gemini e a restaura ao reenviar o mesmo conjunto de chamadas,
preservando conteúdo, ordem e assinaturas opacas. Esses dados ficam na memória
da análise, sem logs ou banco; também contam no teto de caracteres. Uma chamada
de ferramenta produzida por outro provedor não possui esse registro: a tentativa
Gemini é recusada localmente, sem fabricar assinatura ou repetir a ferramenta.
Isso limita fallback **para** Gemini durante um ciclo de ferramentas de outro
provedor; a próxima alternativa, se houver, pode prosseguir. Fallback **do** Gemini
para outros provedores remove os metadados exclusivos do Google.

Os testes de CI simulam HTTP; disponibilidade, cotas e qualidade da interpretação
exigem homologação real. Tokens de raciocínio/cache continuam sem detalhamento;
os totais seguem os campos `prompt_tokens` e `completion_tokens` recebidos.

Referências oficiais consultadas em 07/11/2026:
[compatibilidade OpenAI](https://ai.google.dev/gemini-api/docs/openai) e
[assinaturas de ferramentas](https://ai.google.dev/gemini-api/docs/thought-signatures).

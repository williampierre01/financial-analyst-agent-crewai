# Etapa 2 — API local de análises

## O que foi implementado

FastAPI fornece início e consulta de análises, reutilizando run_analysis_result.
O Gradio permanece independente e continua funcionando. A interface React ainda
não foi criada. Novos módulos estão em backend/api e backend/services; os módulos
financeiros existentes permanecem na raiz para evitar uma movimentação ampla.

## Executar no Windows

Abra PowerShell na pasta do projeto:

```powershell
cd "C:\Users\will\Documents\Codex\2026-10-13\lis\work\financial-analyst-agent-crewai"
& .\.venv\Scripts\uv.exe sync --locked
& .\.venv\Scripts\uv.exe run --locked uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Mantenha esse terminal aberto. A documentação interativa está em
http://127.0.0.1:8000/docs e a verificação do serviço em
http://127.0.0.1:8000/health. A página /docs é uma ferramenta de teste, não a
nova interface do produto. Use Ctrl+C para encerrar após as análises terminarem.

Não use múltiplos workers: o armazenamento é local a um único processo.
Reinícios, encerramento e recarga automática apagam os identificadores e dados.
O comando usa somente o endereço local do computador. Esta versão não tem
login, isolamento por usuário ou configuração CORS para o futuro front-end.

## Testar pela documentação interativa

1. Abra /docs, expanda GET /health, clique em Try it out e Execute. Deve retornar
   200 e status ok; isso verifica apenas a API, sem testar Yahoo ou IA.
2. Expanda POST /analyses e envie {"ticker": "PETR4"}. Esse passo inicia uma
   análise real, com Yahoo, notícias e IA conforme a configuração do .env.
3. A resposta 202 contém id; copie esse valor. O cabeçalho Location também
   informa o caminho de consulta. Não envie outro POST apenas para atualizar.
4. Em GET /analyses/{analysis_id}, informe o id e execute. Repita a consulta
   a cada dois segundos, até status completed ou failed.
5. Durante o processamento, data pode estar preenchido enquanto interpretation
   permanece null. Os avisos da fonte ficam em data.warnings; erros da execução
   ficam em errors. Se a IA falhar, os dados coletados são preservados.

A resposta inicial é uma fotografia da aceitação da tarefa, normalmente sem
dados; use GET para obter o estado atual. Cada POST aceito cria uma tarefa nova,
mesmo com o mesmo ticker. A API ainda não implementa idempotência nem cache.

## Testar pelo PowerShell

Em outro terminal, com a API aberta:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$analise = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/analyses -ContentType 'application/json' -Body '{"ticker":"PETR4"}'
$analise.id
Invoke-RestMethod "http://127.0.0.1:8000/analyses/$($analise.id)" | ConvertTo-Json -Depth 20
```

Execute novamente apenas a última linha para atualizar. Isso não coleta dados
ou chama a IA novamente; lê o resultado da tarefa já iniciada.

## Contrato HTTP

| Rota | Resultado |
|---|---|
| GET /health | 200, serviço ativo e limites do armazenamento |
| POST /analyses | 202, identificador e estado inicial; Location aponta para consulta |
| GET /analyses/{analysis_id} | 200, estado mais recente ou resultado terminal |
| GET /openapi.json | Esquemas de requisições, respostas e dados financeiros |

Entrada: objeto com apenas ticker, string até 16 caracteres. Normaliza espaços,
letras minúsculas e sufixo .SA. AAPL, vazio, valores não textuais e campos extras
são rejeitados antes de qualquer execução.

Respostas de análise incluem id (UUID), created_at, updated_at, expires_at,
ticker, status, stage, data, interpretation_status, interpretation e errors.
Datas e horários são ISO 8601 em UTC; data mantém o contrato financeiro v3.
expires_at é null durante o trabalho e preenchido ao encerrar o worker.

- status: running, completed ou failed, referente ao processamento.
- data.status: complete, partial ou unavailable, referente aos dados.
- interpretation_status: pending, running, completed, failed ou skipped.
- stage: gathering, quant, cio ou done.

completed não significa que a IA funcionou: falha na interpretação pode resultar
em completed + interpretation_status=failed. Ausência de dados gera completed +
data.status=unavailable + interpretation_status=skipped. Exceções inesperadas
no worker produzem failed e mensagem segura, preservando dados já publicados.

| Código HTTP | Situação |
|---|---|
| 422 | Corpo inválido, ticker fora do formato aceito ou identificador inválido |
| 404 | Identificador desconhecido, expirado ou perdido em reinício |
| 429 | Limite de execução simultânea ou armazenamento atingido |
| 503 | Serviço encerrando ou incapaz de agendar o trabalho |

Erros de execução da análise aparecem no recurso consultado com HTTP 200;
o código HTTP informa se a consulta funcionou, e status/errors informam o
resultado do trabalho. Erros 422 seguem o formato padrão de validação FastAPI.

## Limites desta etapa

- Máximo de 2 análises simultâneas; não há fila ilimitada.
- Máximo de 100 registros retidos, incluindo trabalhos ativos.
- Resultados terminados expiram após 1 hora. A limpeza ocorre no próximo
  acesso de criação/consulta. Trabalhos ativos nunca expiram por esse prazo.
- Dados e controle ficam em memória; não usar mais de um processo/instância.
- Limites são definidos no serviço; create_app permite ajustes nos testes.
- Não há timeout global nem cancelamento: tarefas travadas podem ocupar uma
  vaga indefinidamente. Fechar o navegador não encerra uma tarefa. O encerramento
  normal aguarda os workers; threads em Python não são canceladas à força.
- Antes de disponibilizar para múltiplos usuários: armazenamento compartilhado,
  execução de tarefas com timeout/cancelamento, autenticação e isolamento.

## Testes e validação

Todos os testes, sem chamadas reais aos serviços externos:

```powershell
& .\.venv\Scripts\uv.exe run --locked python -m unittest discover -s tests -v
```

Somente API:

```powershell
& .\.venv\Scripts\uv.exe run --locked python -m unittest discover -s tests -p test_api.py -v
```

Nesta etapa: 52 testes aprovados (14 novos da API). Cobrem validação, coleta
única por tarefa no fluxo existente, consulta sem reexecução, dados antes da IA,
falhas, ausência de dados, capacidade, expiração, reinício e isolamento de cópias.
Uvicorn também foi iniciado localmente: /health respondeu HTTP 200 e o esquema
OpenAPI apresentou as três rotas. Não foi feita análise real com LLM nesta
validação, publicação em nuvem ou execução remota da integração contínua.

FastAPI e Uvicorn passam a ser dependências diretas, preservando as versões já
instaladas. httpx2 é declarado no grupo dev para o TestClient do Starlette
presente no lock. requirements.txt foi regenerado a partir do lock.

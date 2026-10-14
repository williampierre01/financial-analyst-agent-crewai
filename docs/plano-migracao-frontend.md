# Plano de migração gradual da interface

Data: 13/10/2026. Repositório: financial-analyst-agent-crewai.

## Decisão

Adotar React + TypeScript para a interface, FastAPI em Python para comunicação
com o navegador e preservar Python, yfinance, validações e agentes na análise.
Manter um único repositório. Gradio continua funcionando durante a transição.

## Regras preservadas

- Yahoo Finance é a única fonte financeira; foco inicial em ações brasileiras.
- Uma coleta financeira por análise, compartilhada com a interface e os agentes.
- Contrato financeiro v3 permanece: fonte, moeda, período, ausências e avisos.
- Não inventar números, datas ou moedas; dados parciais continuam utilizáveis.
- Dados financeiros e interpretação por IA são independentes.
- Chaves ficam no servidor. A interface não recebe credenciais.

## Preparação entre etapas 1 e 2

Consolidar o ambiente antes de criar a API: Python 3.13.9, dependências diretas
em pyproject.toml, versões e hashes em uv.lock, exportação requirements.txt e
verificação contínua em Windows/Linux. Consulte
[o procedimento de ambiente](ambiente-desenvolvimento.md).

## Etapas e critérios de conclusão

### 1. Separar análise e apresentação — implementada localmente

Criar um resultado estruturado e notificações de progresso, mantendo o adaptador
Markdown e o Gradio. Publicar dados antes da interpretação e preservar a tabela
em falhas da IA. Não mover todos os arquivos nem criar API nesta etapa.

Entrega: analysis_models.py define AnalysisResult; agents.run_analysis_result
executa e publica estados; presentation.py adapta o resultado para Markdown;
app.py consome os estados. agents.run_analysis mantém a saída textual anterior.

Critérios: suíte existente aprovada, coleta única, estados independentes,
atualizações isoladas de mutações e tabela disponível durante a interpretação.
Validação local: 38 testes aprovados, incluindo esses cenários. Testes utilizam
serviços externos simulados; não validam disponibilidade real de Yahoo ou LLM.

### 2. Criar API FastAPI — implementada localmente

Definir contratos HTTP, iniciar uma análise, devolver identificador, consultar
andamento/resultado e disponibilizar verificação de saúde. Rotas propostas:
POST /analyses, GET /analyses/{id}, GET /health. Contratos implementados e documentados em [API local](api-local.md). Consultas periódicas pelo navegador serão suficientes inicialmente.

Separar processamento de qualidade dos dados. A primeira implementação local
pode guardar tarefas em memória; isso perde resultados após reinício e exige
um único processo. Antes de produção, definir persistência, fila de execução,
limites, expiração, isolamento entre usuários e tratamento de reinícios.

Critério atendido localmente: API entrega dados antes da IA, comunica falhas
com códigos seguros e permite consultar o estado terminal sem executar uma
segunda análise. Limites: 2 trabalhos simultâneos, 100 registros e retenção
de uma hora após término; um único processo e nenhuma persistência.
Validação: 52 testes aprovados e inicialização HTTP local confirmada.

### 3. Criar interface React + TypeScript — implementada localmente

Uma página inicial: consulta, andamento em português, resumo do ativo,
qualidade dos dados, exercícios lado a lado e interpretação independente.
Gerar tipos a partir do contrato da API quando viável. Não usar dados fictícios
como se fossem dados reais. Estados vazios, de falha e de carregamento explícitos.

Critérios implementados: consulta, progresso, dados antecipados, falhas
independentes e apresentação responsiva. Contratos TypeScript gerados do
OpenAPI. Guia de execução e validação: [interface React](frontend-local.md).
Gradio permanece em paralelo; implantação e validação operacional são etapa 4.

### 4. Integração e publicação — preparação implementada; publicação pendente

Testar ponta a ponta, concorrência, tempo máximo, reinício e configuração.
Definir infraestrutura compatível com tarefas longas e acesso de usuários.
Verificar responsividade, acessibilidade, credenciais e documentação operacional.
Preparar retorno à versão anterior. Não assumir que desconectar o navegador
cancela trabalho em execução: cancelamento requer implementação própria.

Preparação: React compilado e FastAPI na mesma origem, proteção HTTP Basic
para acesso restrito, scripts para o serviço Python existente no Render,
testes integrados com HTTP real e limite de 600 segundos para o resultado.
O timeout preserva dados, mas não interrompe threads: a vaga permanece ocupada
até a execução terminar. Não há cancelamento forçado nem persistência.

Operação e retorno: [publicação restrita no Render](publicacao-render.md).
Pendente: aplicar as configurações no Render, validar a publicação com os
provedores reais e confirmar o retorno. O Gradio continua como interface
publicada até essa mudança explícita. A etapa 4 não está encerrada.

Critério: publicação reproduzível e comportamento documentado em falhas.

### 5. React como interface principal — pendente

Publicar a nova interface após validação, atualizar instruções e manter Gradio
como apoio temporário. Remover Gradio em uma alteração separada, se desejado.

Critério: React e FastAPI atendem o fluxo principal com testes e documentação.

## Estrutura de destino

```text
backend/
  api/          # Rotas e contratos HTTP
  services/     # Execução e acompanhamento
  financial/    # Fonte e validações
  agents/       # Interpretação
  tests/
frontend/
  src/
    components/
    pages/
    services/
    types/
  tests/
docs/
README.md
```

Mover arquivos gradualmente, com imports, comandos e testes ajustados juntos.
Organização inicial em módulos na raiz é transitória, para reduzir mudanças
simultâneas. Proposta: um PR por etapa; dividir interface visual e integração
se necessário. Publicação não é consequência automática deste documento.

## Fora da primeira migração

Login, histórico permanente para usuários, comparação de empresas, outros
mercados/provedores e gráficos históricos. Gráficos de preços dependem de uma
nova coleta que o contrato atual não fornece.

## Contrato interno da etapa 1

AnalysisResult.to_dict() produz uma cópia serializável em JSON:

| Campo | Significado |
|---|---|
| ticker | Código normalizado, por exemplo PETR4.SA |
| status | running, completed ou failed: execução do serviço |
| stage | gathering, quant, cio ou done: etapa atual |
| data | Snapshot financeiro v3; null antes da coleta ou em falha inesperada |
| data.status | complete, partial ou unavailable: qualidade financeira |
| data.warnings | Limitações da fonte e dos dados |
| interpretation_status | pending, running, completed, failed ou skipped |
| interpretation | Texto da IA ou null |
| errors | Lista de códigos e mensagens seguros de execução |

completed significa que o serviço encerrou seu fluxo; não garante dados
completos nem interpretação bem-sucedida. Ausência de dados resulta em
completed + unavailable + skipped. Falha da IA resulta em completed +
interpretation_status=failed, mantendo data. Uma exceção inesperada na coleta
resulta em failed + skipped e erro data_fetch_failed.

on_update recebe cópias independentes a cada mudança. A primeira atualização
não tem dados; a seguinte publica a coleta antes de iniciar MCP/LLM. Falhas do
observador são registradas sem interromper a análise. O callback legado
on_stage continua notificando quant e cio. Entrada inválida gera ValueError
antes da coleta; o Gradio apresenta a orientação ao usuário.

Ainda não há identificadores, armazenamento de tarefas, timeout global nem
cancelamento. A API e esses controles serão tratados nas etapas seguintes.

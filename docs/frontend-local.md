# Etapa 3 — interface React + TypeScript

## Entrega

Uma interface própria para consultar ações brasileiras, conectada à API da
etapa 2. O Gradio continua disponível em paralelo. Não houve implantação em
nuvem nem substituição do aplicativo publicado.

A tela oferece consulta por código, etapas de processamento, cotação com data,
resumo anual, demonstrativos por grupo com exercícios lado a lado, limitações
da fonte e interpretação por IA independente. Não apresenta histórico de preços
ou gráficos de cotação: esses dados ainda não fazem parte do contrato.

## Ambiente

- Backend: Python 3.13.9 e uv 0.11.33, como nas etapas anteriores.
- Front-end: Node 22.17.1 (frontend/.nvmrc), npm 10.9.2.
- React, TypeScript, Vite e ferramentas têm versões exatas no package.json.
- package-lock.json trava dependências transitivas. Instale com npm ci.
- TypeScript 5.9.3 foi escolhido pela compatibilidade com openapi-typescript.
- node_modules, dist, relatórios e capturas de testes ficam fora do Git.

Node/npm são separados do .venv. A ativação automática do .venv não prejudica
os comandos npm. Use npm.cmd no PowerShell para evitar bloqueio do npm.ps1.

## Executar — dois terminais

### Terminal 1: API Python

Na raiz do projeto:

```powershell
cd "C:\Users\will\Documents\Codex\2026-10-13\lis\work\financial-analyst-agent-crewai"
& .\.venv\Scripts\uv.exe sync --locked
& .\.venv\Scripts\uv.exe run --locked uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Se a API já estiver aberta na porta 8000, use o processo existente. Não execute
múltiplos workers: o armazenamento continua em memória. As chaves de IA seguem
no .env da raiz do backend; não copie nenhuma chave para o front-end.

### Terminal 2: interface React

```powershell
cd "C:\Users\will\Documents\Codex\2026-10-13\lis\work\financial-analyst-agent-crewai\frontend"
node --version
npm.cmd --version
npm.cmd ci
npm.cmd run dev
```

Abra **http://127.0.0.1:5173**. Os dois terminais precisam permanecer abertos.
Para encerrar, use Ctrl+C em cada um, observando que a API aguarda trabalhos
ativos. Não precisa iniciar o Gradio para usar a interface React.

Se a porta 5173 estiver ocupada, pare o processo antigo ou escolha outra:
`npm.cmd run dev -- --port 5174`.

O navegador acessa /api na origem da interface. O Vite encaminha as chamadas
para http://127.0.0.1:8000; não foi habilitado CORS aberto no Python. Para uma
porta de API diferente, defina API_TARGET no terminal do front-end antes de
iniciar, por exemplo `$env:API_TARGET = "http://127.0.0.1:8001"`.
Essa variável configura o servidor de desenvolvimento, não recebe credenciais.

## Testar manualmente

1. Envie campo vazio ou AAPL: deve aparecer orientação, sem criar uma análise.
2. Clique num exemplo ou digite PETR4; clique em Analisar ação. Os exemplos
   apenas preenchem o campo, sem disparar consultas automaticamente.
3. Acompanhe as etapas. A tabela aparece antes da interpretação ficar pronta.
4. Confira moeda, exercício e data da cotação. Horários são apresentados em
   Brasília, com a origem preservada no contrato da API.
5. Alterne Em milhões / Valores integrais nos demonstrativos. Lucro por ação
   nunca é dividido por milhão. Valores não nulos abaixo de 10 mil são exibidos
   em unidades mesmo na opção Em milhões, evitando arredondamento para zero.
6. Confira avisos quando houver dados parciais ou cotação antiga/sem data.
7. Sem interpretação, a tabela permanece. As mensagens orientam conferir os
   serviços de IA sem expor detalhes internos ou chaves.
8. Reduza a largura da janela: os cartões se reorganizam e tabelas podem ser
   percorridas horizontalmente. Use Tab para navegar e Enter para enviar.

Os testes automatizados abaixo exercitam falhas sem alterar suas chaves.
Uma análise real usa Yahoo, notícias e serviços de IA conforme o .env e pode
consumir créditos. Os valores fictícios dos testes não são usados pelo app.

## Acompanhamento e recuperação

- Apenas um POST por envio; o botão fica indisponível durante o acompanhamento.
- GET consulta o estado a cada dois segundos, sem requisições sobrepostas.
- Falhas de GET são tentadas novamente até três vezes. Depois, o acompanhamento
  pausa e oferece retomada pelo mesmo identificador, mantendo os dados exibidos.
- Timeout de POST não dispara outro POST automaticamente: o trabalho pode ter
  sido aceito. A tela explica essa incerteza.
- O identificador ativo fica em sessionStorage, permitindo retomar ao recarregar
  a mesma aba. Não há histórico persistente e o resultado final não é armazenado
  no navegador. Bloqueio de armazenamento não impede uma consulta normal.
- 404 sinaliza expiração ou reinício. A tabela já recebida permanece até iniciar
  nova consulta; um novo POST cria outro trabalho.
- Fechar a tela, pausar acompanhamento ou iniciar outra consulta não cancela um
  trabalho no backend. Os limites da etapa 2 continuam valendo.

Antes de executar npm ci novamente, pare o servidor do front-end com Ctrl+C.
No Windows, o servidor em execução pode manter bibliotecas abertas e impedir
a reinstalação. Pare também processos de testes de navegador que você iniciou.

## Testes automatizados

Na raiz do projeto:

```powershell
& .\.venv\Scripts\uv.exe run --locked python -m unittest discover -s tests -v
& .\.venv\Scripts\uv.exe run --locked python -m backend.api.export_schema --check
```

Na pasta frontend:

```powershell
npm.cmd ci
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd test
npm.cmd run format:check
```

Playwright inicia a interface para os testes. As respostas financeiras e de IA
são simuladas no navegador; não é necessário iniciar a API para essa suíte.
Na primeira instalação, o navegador de testes é baixado separadamente.
O teste de celular usa emulação Chromium, não um aparelho físico nem Safari.

Nesta máquina, os navegadores de teste foram instalados em uma pasta de trabalho
separada. Para reutilizá-los sem novo download, antes de npm test execute:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "C:\Users\will\Documents\Codex\2026-10-13\lis\work\playwright-browsers"
```

Cobertura: entrada inválida, andamento, resposta parcial, ausência de dados,
valores nulos/zero/negativos, mudança de escala, falha da IA, capacidade,
expiração, recuperação da conexão, retomada pelo id e Markdown sem HTML ativo.
Também há verificações automáticas WCAG A/AA nas telas inicial e preenchida;
isso não substitui uma auditoria completa de acessibilidade.

## Contrato Python / TypeScript

A fonte do contrato é FastAPI. Após alterar seus schemas, na raiz execute:

```powershell
& .\.venv\Scripts\uv.exe run --locked python -m backend.api.export_schema
npm.cmd run types:generate --prefix frontend
```

Versione frontend/openapi.json e frontend/src/types/api.generated.ts junto
com a alteração Python. Não edite os tipos gerados manualmente. O workflow
confere o JSON contra a API e os tipos contra esse JSON, além de instalar pelo
lock, compilar e executar testes do navegador.

## Build e próxima etapa

`npm.cmd run build` gera frontend/dist. `npm.cmd run preview` permite conferir
o build local em http://127.0.0.1:4173, com o mesmo encaminhamento para a API.
Vite dev/preview são ferramentas locais; para publicar será necessário servir
o build e encaminhar /api a FastAPI na infraestrutura escolhida.

Persistência, autenticação, timeout/cancelamento de tarefas e implantação ficam
para a etapa 4. Gradio permanece disponível pelo comando python app.py.

## Validação desta entrega

- 52 testes Python aprovados.
- 18 testes de navegador aprovados: 9 cenários em desktop e celular emulado.
- Verificação automática de acessibilidade sem violações detectadas nas telas
  inicial e preenchida, para as regras WCAG A/AA selecionadas.
- Capturas de tela revisadas em desktop e celular.
- npm ci, compilação TypeScript/Vite e verificação de formatação aprovados.
- Contratos OpenAPI/TypeScript regenerados e conferidos.
- Encaminhamento Vite para FastAPI real verificado: saúde HTTP 200 e rejeição
  de ticker inválido HTTP 422, sem iniciar consultas aos provedores.
- Nenhuma chamada real a Yahoo/IA, publicação em nuvem ou execução remota do
  novo workflow realizada nesta etapa. Os testes de resultados usam simulação.

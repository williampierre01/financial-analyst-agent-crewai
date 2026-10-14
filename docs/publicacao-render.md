# Etapa 4 — preparação para publicação restrita no Render

## Estado e escopo

Publicado no Render em 14/10/2026, commit 7901396. O usuário confirmou a
solicitação de usuário e senha e apresentou a consulta PETR4 com dados antes
da interpretação, seguida do relatório. React é a interface principal;
Gradio permanece como apoio temporário no repositório.

Em 14/10/2026, foram confirmados reinício com nova análise PETR4, rollback
para b839261 e restauração de b725d5b como Live. Carregamento e senha foram
conferidos nas três situações. O rollback foi entre versões React; retorno ao
Gradio não foi executado. Veja o registro de homologação para os limites do teste. As correções adiadas
estão em [pendências de homologação](pendencias-homologacao.md). O sucesso do
fluxo não constitui validação da precisão financeira ou das afirmações da IA.
As seções abaixo documentam como reproduzir a configuração e os testes restantes.

O destino escolhido é o serviço Python existente no Render, inicialmente com
acesso restrito. O build React e a API são servidos pelo mesmo processo Python:

- `/`: interface compilada; `/assets/`: recursos da interface.
- `/api/analyses`: iniciar análise; `/api/analyses/{id}`: acompanhar.
- `/api/docs` e `/api/health`: documentação e estado da API, também protegidos.
- `/healthz`: somente `{"status":"ok"}`, público para a plataforma.

Não é necessário executar Vite no servidor. O ponto de entrada de publicação é
`backend.web:app`; `backend.api.main:app` continua sendo a API de desenvolvimento
sem autenticação e não deve ser usado para essa publicação restrita.

## Acesso restrito

HTTP Basic apresenta uma solicitação nativa de usuário e senha no navegador.
Configure `WEB_USERNAME` e `WEB_PASSWORD` apenas no servidor. A senha deve ter
pelo menos 16 caracteres e o usuário não pode conter `:`. Use caracteres ASCII
(sem acentos) no usuário e na senha, conforme o parser HTTP Basic utilizado. Configuração ausente
ou inválida impede a inicialização; não existe senha padrão nem fallback público.

Use HTTPS no Render. Uma credencial compartilhada serve para um grupo de teste
confiável: não representa contas individuais, permissões ou isolamento de
resultados entre pessoas. Quem possui acesso pode consultar um identificador
de análise que conheça. Não existe botão de logout; o navegador pode conservar
credenciais Basic durante a sessão. Uma janela privada separada ajuda nos testes;
para revogar acesso, troque a senha e reinicie o serviço.

Interface, API, documentação e arquivos estáticos exigem autenticação. Escritas
com origem externa são recusadas. As chaves de IA não entram no JavaScript.
O build não usa variáveis `VITE_*` com segredos e não copia o `.env` para `dist`.

## Rodar a versão unificada no Windows

Na raiz do repositório, com Python/Node já preparados conforme os guias anteriores:

```powershell
& .\.venv\Scripts\uv.exe sync --locked
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
$env:WEB_USERNAME = Read-Host 'Usuário para acesso local'
$senhaLocal = Read-Host 'Senha (mínimo de 16 caracteres)' -AsSecureString
$env:WEB_PASSWORD = [System.Net.NetworkCredential]::new('', $senhaLocal).Password
& .\.venv\Scripts\python.exe -m uvicorn backend.web:app --host 127.0.0.1 --port 8000 --workers 1
```

Abra **http://127.0.0.1:8000** e informe a credencial escolhida. O servidor
precisa permanecer aberto. A senha não é salva no repositório. Após Ctrl+C:

```powershell
Remove-Item Env:WEB_USERNAME, Env:WEB_PASSWORD
Remove-Variable senhaLocal
```

Se a porta estiver ocupada, use `--port 8001` e abra essa porta. Como interface e
API compartilham a origem, não é necessário configurar `API_TARGET` nesse modo.
Uma análise real utiliza Yahoo e os serviços de IA já configurados no backend.

## Preparar o serviço existente no Render

Antes da troca, registre no painel o commit implantado e os comandos atuais de
build/start, caminho de health check e versões. Não copie valores de secrets
para documentos. Desative a publicação automática durante a homologação para
que um merge posterior não provoque uma troca inesperada.

Depois de revisar e integrar esta alteração, configure o serviço Python existente:

| Configuração | Valor |
|---|---|
| Runtime | Python, mantendo o serviço existente |
| Branch | `main`, após o merge deste trabalho |
| Root Directory | Raiz do repositório |
| Build Command | `bash scripts/render-build.sh` |
| Start Command | `bash scripts/render-start.sh` |
| Health Check Path | `/healthz` |
| `PYTHON_VERSION` | `3.13.9` |
| `NODE_VERSION` | `22.17.1` |
| `WEB_USERNAME` | Usuário privado escolhido no painel |
| `WEB_PASSWORD` | Senha forte com pelo menos 16 caracteres, no painel |
| Secrets de IA | Preservar os já utilizados pelo backend |

O Node selecionado inclui npm 10.9.2; o script valida as duas versões antes de
compilar. O uv 0.11.33 é instalado por requirements-tooling.txt e utiliza o
uv.lock com `--locked --no-dev`. O npm usa `npm ci` e package-lock.json.
O start lê `PORT` do ambiente da plataforma e usa exatamente um worker.
Não configure múltiplas instâncias/autoscaling com este armazenamento em memória.

O script aceita cabeçalhos encaminhados pelo proxy do Render para reconhecer
HTTPS e conferir a origem. Ele é específico desse ambiente; localmente use o
comando com `127.0.0.1` acima, sem confiar em proxies arbitrários.

Não foi adicionado um Blueprint automático: a troca depende da configuração
explícita do serviço existente. A instalação deve caber nos recursos do plano;
memória, disponibilidade de Yahoo e latência da IA precisam ser medidas na nuvem.

## Homologação após publicação

1. Em janela privada, `/healthz` responde 200 sem credenciais e `/` solicita senha.
2. Sem senha, `/api/health`, `/api/docs` e POST `/api/analyses` respondem 401.
3. Com senha correta, a interface abre e os arquivos estáticos carregam sem erro.
4. Consulte PETR4 e confira dados antes da interpretação, fonte, moeda e períodos.
   Essa consulta usa provedores reais e pode consumir créditos de IA.
5. Verifique o comportamento se a IA ou o Yahoo estiverem indisponíveis. Ausência
   de dados é um resultado explícito, não motivo para inventar números.
6. Recarregue a aba durante uma análise: o acompanhamento retoma o mesmo id.
7. Reinicie o serviço em uma janela de teste: o id anterior retorna 404, a
   interface explica a perda da consulta e permite uma nova. Resultados em memória
   não sobrevivem a deploy, suspensão ou reinício.
8. Teste o retorno abaixo e registre commit, horário e resultado antes de encerrar
   a homologação. Só então decida sobre publicação automática/interface principal.

## Limites e falhas

- Até 2 trabalhos ativos, 100 registros e retenção de 1 hora após a saída do worker.
- Prazo do resultado: 600 segundos. Ao excedê-lo, o cliente recebe
  `analysis_timeout`, estado `failed` e os dados já publicados permanecem.
- O timeout não mata a thread nem garante interrupção de chamadas/cobranças dos
  provedores. Resultados tardios não sobrescrevem o erro de timeout.
- A vaga não é liberada até o worker sair; o registro em timeout fica sem
  `expires_at` nesse intervalo. Assim, novas consultas não acumulam threads travadas.
- Se as duas vagas ficarem presas, a API devolve 429 para novos trabalhos. Um
  reinício operacional pode ser necessário e perde todas as consultas em memória.
- O encerramento normal aguarda threads ativas. Não há prazo garantido de
  desligamento gracioso; a plataforma pode encerrar o processo à força. O health
  check confirma que o servidor responde, não disponibilidade de Yahoo/IA/vagas.
- Fechar o navegador não cancela análise. Não existe fila persistente, histórico
  permanente, cancelamento forçado, login individual ou isolamento entre usuários.

Esse escopo permite um piloto restrito. Abertura pública ou escala exige outra
etapa com execução isolada, fila/persistência e autenticação individual.

## Retorno ao Gradio

Restaure os comandos e health check registrados antes da troca e selecione o
commit anterior no Render. Não basta voltar o commit mantendo
`scripts/render-start.sh`: o commit antigo não contém esse arquivo. Preserve
as chaves anteriores. Verifique o Gradio após o retorno e confirme que os
resultados transitórios foram descartados. O Gradio não passa pela proteção
Basic de backend.web: mantenha o nível de acesso anterior em mente ao retornar.

## Testes automatizados

Na raiz:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -m backend.api.export_schema --check
npm.cmd run build --prefix frontend
npm.cmd test --prefix frontend
npm.cmd run test:integration --prefix frontend
npm.cmd run format:check --prefix frontend
```

Instale antes o Chromium do Playwright conforme o guia do frontend. Nesta máquina,
reutilize `PLAYWRIGHT_BROWSERS_PATH` indicado naquele guia. Deixe a porta 8012
livre: os testes integrados iniciam seu próprio servidor e recusam reaproveitar
um processo existente.

Os testes integrados usam o build real, autenticação e HTTP FastAPI reais;
somente o executor financeiro/IA é substituído por cenários controlados em
tests/integration_server.py. Esse executor não é importado pela aplicação normal.
A suíte verifica dados antecipados, limite de concorrência, falha e timeout.
Testes Python cobrem reinício, retenção, proteção de rotas e configuração inválida.

## Referências de configuração

- [Runtimes nativos do Render](https://render.com/docs/native-runtimes)
- [Versão de Node no Render](https://render.com/docs/node-version)
- [Porta e serviço web](https://render.com/docs/web-services)
- [Health checks](https://render.com/docs/health-checks)
- [HTTP Basic no FastAPI](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/)

## Resultado da validação local

57 testes Python, 18 testes de interface e 3 testes integrados aprovados.
Build, formatação, contrato OpenAPI e sintaxe dos scripts Bash conferidos.
Os testes automatizados não fizeram chamadas reais a Yahoo/IA. A publicação
e a consulta real posteriores foram confirmadas pelo usuário conforme o estado
registrado no início deste documento.

No ambiente restrito do agente no Windows, a finalização automática dos
servidores pelo Playwright ficou presa. As suítes foram repetidas com os mesmos
servidores de teste gerenciados separadamente e finalizaram com código zero;
os processos foram encerrados após a verificação. A configuração normal de
inicialização/encerramento ainda precisa ser confirmada no CI Linux e no terminal
do desenvolvedor, fora desse ambiente restrito.

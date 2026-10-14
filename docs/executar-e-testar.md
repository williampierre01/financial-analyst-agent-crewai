# Como executar e testar — Windows / PowerShell

## 1. Abrir o projeto

Abra o PowerShell ou o terminal do editor e execute:

```powershell
cd "C:\Users\will\Documents\Codex\2026-10-13\lis\work\financial-analyst-agent-crewai"
```

Use a branch da alteração em teste ou a main após o merge. Não é necessário
instalar React ou Node nesta etapa: a interface continua sendo o Gradio.

## 2. Sincronizar o ambiente controlado

O projeto usa Python **3.13.9** e uv **0.11.33**. Neste computador, uv já está
disponível no ambiente existente. Na pasta do projeto, execute:

```powershell
& .\.venv\Scripts\uv.exe sync --locked
& .\.venv\Scripts\python.exe --version
```

O comando usa as versões de uv.lock e remove bibliotecas extras que não fazem
parte do projeto. Feche o aplicativo antes de sincronizar. Nenhum arquivo de
código ou .env é removido. Se o lock estiver desatualizado em relação ao
pyproject.toml, o comando falha em vez de alterar versões silenciosamente.

Em uma instalação nova, primeiro instale a ferramenta no Python do computador
(fora de um ambiente virtual ativo):

```powershell
py -m pip install --user -r requirements-tooling.txt
py -m uv sync --locked
```

O uv encontra ou baixa o Python 3.13.9 indicado por .python-version e cria o
.venv. Esses comandos precisam de internet na primeira instalação. Se o
comando py não existir, instale o Python e o launcher para Windows primeiro.
Consulte [o guia de ambiente](ambiente-desenvolvimento.md) para atualizações.

Os próximos comandos usam o executável da .venv diretamente: não exigem
ativação nem mudança de política do PowerShell.

## 3. Configurar a interpretação por IA (opcional para testar dados)

Para a análise completa, crie ou edite o arquivo .env na raiz do projeto:

```dotenv
DEEPSEEK_API_KEY=sua_chave_deepseek
GROQ_API_KEY=sua_chave_groq
```

Substitua os exemplos por suas próprias chaves. O código atual espera as duas
variáveis. O arquivo .env é ignorado pelo Git; não coloque chaves em arquivos
versionados. Chamadas reais de IA estão sujeitas às condições dos provedores.

Yahoo Finance não exige chave neste aplicativo. Sem as chaves de IA, você pode
consultar os dados; a interpretação indicará indisponibilidade. Reinicie o
aplicativo após alterar as variáveis.

## 4. Rodar a interface

```powershell
& .\.venv\Scripts\python.exe app.py
```

Mantenha o terminal aberto e acesse http://localhost:7860 no navegador.
Se PORT estiver configurada no seu ambiente, use a porta exibida no terminal.
Para parar o servidor, pressione Ctrl+C. Para escolher outra porta:

```powershell
$env:PORT = "7861"
& .\.venv\Scripts\python.exe app.py
```

Nesse caso, acesse http://localhost:7861. O comando atual escuta em 0.0.0.0,
portanto pode aceitar conexões de rede conforme o firewall; não há login.

## 5. Testar pela tela

1. Envie o campo vazio ou AAPL. Deve aparecer orientação para código da B3,
   sem iniciar a análise.
2. Digite petr4 ou PETR4.SA. Ambos devem consultar PETR4.SA.
3. Observe a coleta. Quando os dados chegarem, a tabela deve aparecer enquanto
   a interpretação ainda está em andamento, se houver dados disponíveis.
4. Confira fonte, datas, moedas, campos ausentes e avisos. Dados parciais são
   um resultado possível; não presuma disponibilidade total do Yahoo.
5. Com as chaves válidas, a interpretação deve aparecer abaixo da tabela ao
   terminar. Em falha da IA, a tabela deve permanecer acompanhada de aviso.
6. Repita com VALE3 ou ITUB4. Não é necessário que valores ou disponibilidade
   coincidam com consultas anteriores.

Para verificar falha de IA de forma reproduzível, use os testes automatizados
abaixo; eles simulam a falha sem editar suas chaves nem consumir serviços.

## 6. Rodar todos os testes automatizados

Em outro terminal, na mesma pasta:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado esperado nesta etapa: Ran 38 tests e OK. A suíte não chama Yahoo,
notícias nem serviços de IA reais. Ela testa validações, contrato, adaptadores,
coleta única, progresso, tabela antecipada, isolamento dos estados, falhas de
IA e compatibilidade do relatório textual.

Para rodar apenas os testes de fluxo e da etapa 1:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_analysis_flow.py -v
```

Avisos simulados de interpretação/observador são esperados em testes de erro.
Um aviso de dependência sobre lifespan também foi observado no ambiente; o
resultado final OK é o critério da suíte, não a ausência de mensagens.

## 7. Consultar serviços reais sem IA

```powershell
& .\.venv\Scripts\python.exe test_tools.py PETR4
```

Este comando consulta Yahoo e notícias, exige internet e não chama os LLMs.
Mostra qualidade, cotação, avisos e parte do JSON. Não é um teste automático
com aprovação/reprovação: examine os dados e os avisos apresentados.

## 8. Executar o relatório pelo terminal

```powershell
& .\.venv\Scripts\python.exe agents.py PETR4
```

Essa execução usa os serviços reais e as chaves de IA configuradas. O resultado
continua em Markdown, preservando compatibilidade com a versão anterior.

## Solução de problemas

- Executável não encontrado: confirme a pasta e a existência de .venv.
- Módulo ausente: pare o app e execute `.\.venv\Scripts\uv.exe sync --locked`.
- Porta ocupada: pare o processo anterior ou escolha PORT=7861.
- Dados indisponíveis: confira conexão e avisos; o Yahoo pode limitar consultas.
- Interpretação indisponível: confira as duas chaves, acesso e saldo dos serviços.
- A tela continua aguardando: nesta etapa ainda não existe timeout global nem
  cancelamento; pare com Ctrl+C se necessário. Esse controle é trabalho futuro.

## Escopo da validação realizada

38 testes automáticos aprovados com serviços simulados. O Gradio também foi
iniciado em um teste local de inicialização (credenciais isoladas pelo ambiente
de teste), retornando HTTP 200 e uma página HTML; o servidor foi encerrado
após a verificação. Nenhuma análise paga
com LLM real foi executada nesta entrega. Disponibilidade dos serviços e
qualidade visual no navegador não são comprovadas pela suíte de unidade.

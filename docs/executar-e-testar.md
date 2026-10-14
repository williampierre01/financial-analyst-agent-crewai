# Como executar e testar — Windows / PowerShell

## 1. Abrir o projeto

Abra o PowerShell ou o terminal do editor e execute:

```powershell
cd "C:\Users\will\Documents\Codex\2026-10-13\lis\work\financial-analyst-agent-crewai"
```

As alterações da etapa 1 foram preparadas na branch refactor/structured-analysis.
Para testar esta entrega, use essa branch ou a main após o merge do respectivo PR. Não é necessário instalar React,
Node ou FastAPI nesta etapa: a interface continua sendo o Gradio.

## 2. Usar o ambiente existente

O ambiente .venv deste computador já contém as dependências. Confira:

```powershell
& .\.venv\Scripts\python.exe --version
```

O ambiente usado na validação local é Python 3.13.9. Os comandos abaixo usam
esse executável diretamente, sem exigir ativação nem alteração de políticas
do PowerShell.

Somente para uma instalação nova: instale Python 3.11, crie um ambiente e
instale as dependências (é necessário acesso à internet):

```powershell
py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Não recrie o ambiente já existente para executar este projeto.

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
- Módulo ausente: instale requirements.txt usando o Python da própria .venv.
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

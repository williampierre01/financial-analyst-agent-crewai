# Ambiente de desenvolvimento e controle de dependências

## Decisão e arquivos

Padronizamos Python 3.13.9, a versão utilizada nos testes locais existentes,
e uv 0.11.33 como gerenciador. Não é necessário um ambiente por branch.
A cada troca de branch com mudanças de dependências, sincronize o .venv.

| Arquivo | Papel |
|---|---|
| .python-version | Seleciona Python 3.13.9 para uv e a integração contínua |
| pyproject.toml | Dependências diretas, faixa Python 3.13 e grupo dev |
| uv.lock | Versões exatas transitivas, plataformas e hashes dos pacotes |
| requirements.txt | Exportação do lock para instalações que usam pip |
| requirements-tooling.txt | Versão exata de uv para preparar a ferramenta |
| .github/workflows/tests.yml | Recriação e testes em Windows e Linux |

O grupo dev inclui httpx2 para o TestClient do Starlette usado nos testes HTTP.
unittest continua vindo com o Python. Ferramentas futuras de testes ou análise
estática devem entrar nesse grupo, separadas da execução.
O uv também aparece transitivamente no conjunto atual de execução porque
é exigido por dependências do CrewAI; isso não foi removido à força.

A migração preserva as versões instaladas dos pacotes necessários e não
reintroduz pandas-datareader. O lock não é um pip freeze indiscriminado:
foi resolvido a partir das dependências diretas e dos extras utilizados.

## Neste computador

Na raiz do projeto, com o aplicativo parado:

```powershell
& .\.venv\Scripts\uv.exe sync --locked
& .\.venv\Scripts\uv.exe pip check
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe app.py
```

Ativação automática no editor é apenas uma conveniência. Os caminhos acima
continuam funcionando sem ativação. Não instale pacotes manualmente com pip
no ambiente da aplicação: registre as alterações nos arquivos de controle.

## Em outro computador

Instale o Python e seu launcher. Fora de uma .venv ativa, no repositório:

```powershell
py -m pip install --user -r requirements-tooling.txt
py -m uv sync --locked
py -m uv run --locked python -m unittest discover -s tests -v
py -m uv run --locked python app.py
```

A instalação inicial requer internet e pode baixar o Python selecionado.
O uv é uma ferramenta de preparação; as bibliotecas do app ficam no .venv.
Se uv estiver no PATH, `uv` substitui `py -m uv`. Não copie a pasta .venv entre
computadores: ela depende do sistema e de caminhos locais.

## Desenvolvimento e execução

- `uv sync --locked`: instala o conjunto de desenvolvimento, incluindo dev.
- `uv sync --locked --no-dev`: instala apenas dependências de execução.
- `uv run --locked python app.py`: sincroniza e executa com o lock verificado.
- `uv lock --check`: confere se o lock corresponde ao projeto, sem atualizá-lo.

`--locked` deve ser usado nos fluxos normais e na integração contínua.
A sincronização exata remove pacotes extras. Ela não modifica .env ou código.
Configurar chaves dos serviços continua sendo uma etapa local separada.

## Adicionar ou atualizar uma biblioteca

Faça mudanças em uma branch própria. Exemplos usando uv no PATH; neste
computador pode-se usar `.\.venv\Scripts\uv.exe` no lugar de uv.

```powershell
# Adição de execução (exemplo para uma etapa futura):
uv add nome-da-biblioteca
# Adição de ferramenta de desenvolvimento:
uv add --dev nome-da-ferramenta
# Atualização deliberada de uma biblioteca já utilizada:
uv lock --upgrade-package yfinance
uv sync --locked
uv pip check
uv run --locked python -m unittest discover -s tests -v
# Atualizar a exportação após qualquer mudança no lock:
uv export --locked --no-dev --no-emit-project --no-header --output-file requirements.txt
```

Substitua os nomes ilustrativos. Revise pyproject.toml, uv.lock e requirements.txt
juntos. O arquivo exportado contém versões exatas e hashes; não o edite à mão.
Atualizações globais com `uv lock --upgrade` devem ser planejadas e testadas,
pois podem mudar muitas dependências transitivas de uma vez.
Para mudar a versão do uv, ajuste requirements-tooling.txt e required-version
em pyproject.toml juntos e valide novamente a geração do lock/exportação.

## Publicação e Python

A faixa aceita em pyproject.toml é >=3.13,<3.14; o patch oficial é 3.13.9.
Ao mudar Python, atualize .python-version e a faixa se necessário, resolva o
lock novamente e execute os testes. Não presuma compatibilidade com 3.11.

Em plataformas com uv: configure Python 3.13.9 e uv 0.11.33, instale com
`uv sync --locked --no-dev` e execute com
`uv run --locked --no-dev python app.py`.

Em plataformas que exigem pip, configure Python 3.13.9 e use:

```bash
python -m pip install --require-hashes -r requirements.txt
python app.py
```

A exportação é para execução, sem ferramentas dev. Um ambiente novo evita
pacotes extras: pip install não remove bibliotecas sobrando de instalações
antigas. Confira a versão configurada no provedor, pois pode prevalecer sobre
.python-version. O sdk_version do README foi alinhado ao Gradio 6.30.0 travado.
Não foi realizada implantação em Render ou Hugging Face nesta alteração.

## Verificações automáticas e limites

O workflow tests.yml prepara Python e uv nas versões selecionadas, recria o
ambiente, verifica compatibilidade, confere se requirements.txt corresponde
ao lock e executa a suíte em Windows e Linux. A execução remota só acontece
quando a alteração for enviada ao GitHub; configurar o arquivo não comprova
que a matriz remota passou.

O lock registra alternativas por plataforma; resolução não substitui teste
real em cada sistema. Hashes verificam integridade dos arquivos baixados,
não garantem ausência de vulnerabilidades ou a disponibilidade futura do índice.

O ambiente separado usado na validação fica fora do repositório e não deve
ser enviado ao Git. .venv, caches e .env também ficam fora do versionamento.

Referências: [lock e sincronização](https://docs.astral.sh/uv/concepts/projects/sync/)
e [migração a partir de pip](https://docs.astral.sh/uv/guides/migration/pip-to-project/).

## Validação desta entrega

- Ambiente Windows separado recriado do zero com Python 3.13.9 e 168 pacotes.
- 38 testes aprovados nesse ambiente, sem chamadas reais de IA.
- Lock atualizado e exportação reproduzida sem diferenças.
- Versões das bibliotecas necessárias preservadas em relação ao ambiente anterior.
- .venv principal sincronizado; removidos mcp-types, pandas-datareader e setuptools
  que sobravam da instalação anterior e não são exigidos pelo conjunto resolvido.
- Checagem de compatibilidade aprovada após a sincronização.
- Matriz Windows/Linux do GitHub ainda não executada remotamente.

Os avisos de dependências sobre lifespan e um ResourceWarning de event loop
foram observados na suíte local, sem falhas de testes. Não foram tratados como
parte desta mudança de controle de dependências.

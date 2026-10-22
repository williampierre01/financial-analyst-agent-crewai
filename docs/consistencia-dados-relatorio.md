# Consistência dos dados e do relatório

Escopo aprovado em 21/10/2026 após revisão das capturas de PETR4: moeda e
escala, datas, notícias antigas e largura da leitura. Não amplia a metodologia
para recomendações de compra/venda.

## Correções

- O adaptador usa o mesmo endpoint de séries financeiras do Yahoo acessado pelo
  yfinance, preservando `currencyCode` e `reportedValue.raw` de cada observação.
  O DataFrame do yfinance descarta a moeda por observação; `financialCurrency`
  do cadastro geral não é prova da moeda desses valores.
- Apenas observações do símbolo solicitado e período `12M` são aceitas. Os dois
  encerramentos mais recentes continuam sendo usados. Totais permanecem em
  unidades e EPS permanece por ação, sem multiplicação ou câmbio presumido.
- Moeda ausente ou divergente no demonstrativo fica desconhecida. As verificações
  existentes impedem cálculos com moedas ausentes/incompatíveis, inclusive preço
  em BRL dividido por EPS em USD. Falhas de transporte preservam dados parciais.
- Referências de consulta/cotação fornecidas à IA incluem data e hora em Brasília.
  Datas contábeis de encerramento não sofrem conversão de fuso.
- Notícias com datas informadas são ordenadas da mais nova para a mais antiga.
  Mais de 30 dias recebe rótulo de contexto histórico; data desconhecida fica ao
  final, com atualidade não confirmada. Nada é apresentado como artigo verificado.
  A IA recebe instrução de separar esses grupos e omitir grupos vazios.
- A largura máxima da prosa passa de 80 para 110 caracteres aproximados, mantendo
  adaptação a telas menores e sem alterar tabelas.

## Validação e limites

Testes de regressão preparados para execução apenas no CI: moeda da observação
divergente do cadastro, moeda ausente/mista, símbolo/período incompatível, falha
do provedor, bloqueio de P/L entre moedas, virada de data UTC/Brasília e notícias
históricas/sem data. Nenhum teste ou aplicação foi executado localmente.

A correção não audita a exatidão contábil do Yahoo. A amostra real de PETR4 deve
ser conferida após publicação, incluindo o `currencyCode` retornado pelo provedor.
Não converter os valores das capturas retroativamente por suposição. O acesso ao
transporte interno do yfinance é isolado em `yahoo_statements.py`; alterações da
biblioteca ou do provedor podem tornar os demonstrativos indisponíveis.

A apresentação das datas e grupos no texto ainda depende de geração por IA;
as referências e rótulos são determinísticos, mas não há validação completa da
prosa gerada. Conferir uma nova análise no Render após merge/publicação manual.

Referência técnica: [implementação de séries financeiras do yfinance](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/fundamentals.py).

## Cotação — acompanhamento em 22/10/2026

As capturas após publicação mostram demonstrativos em USD e cotação ausente em
PETR4 e VALE3. A versão instalada do yfinance retira campos de cotação e símbolo
de `get_info()`. O caminho anterior dependia do símbolo desse cadastro, mesmo
quando o preço vinha de `fast_info`, deixando a observação sem identidade válida.

Quando o cadastro não fornece uma observação completa, o adaptador consulta
`get_history_metadata()` e aceita seu mapeamento (inclusive o Mapping lazy da
biblioteca). Símbolo, moeda, preço e horário vêm juntos desse retorno. Símbolo
divergente é rejeitado; horário ausente não é preenchido com horário de outra
resposta nem com o instante da consulta. As regras de atualidade e de moeda
dos cálculos permanecem em vigor. Falhas do Yahoo ainda podem causar ausência.

Regressões no CI cobrem PETR4/VALE3 com cadastro sem campos, Mapping não-dict,
símbolo incompatível e horário ausente. Conferir cotação no Render após deploy;
a causa específica da consulta anterior não pode ser provada só pela captura.

## Contenção do resultado operacional — 22/10/2026

Conferência limitada a Vale e Petrobras, conforme solicitação do usuário. As
divergências e fontes estão em `pendencias-homologacao.md`. Não foi encontrada
uma definição pública suficiente para reconciliar Operating Income do Yahoo
com as linhas oficiais comparadas. Não se concluiu que os valores do provedor
sejam arbitrários: podem refletir ajustes ou classificações ainda não comprovados.

Correção de contenção autorizada: na normalização, qualquer valor desse campo
é substituído por ausência na base entregue à API e aos agentes, em todos os
períodos. O retorno bruto não é alterado. Um aviso explica a falta de conciliação
e o status fica parcial. A política vale para o campo do provedor, sem presumir
que somente os dois tickers examinados estejam sujeitos ao problema.

Não há substituição por números fixos, cálculo alternativo ou nova coleta. Os
demais valores e indicadores calculados pelo código permanecem inalterados.
Instruções de geração proíbem reconstruir o campo e usá-lo para comparações ou
hipóteses com o lucro líquido. A prosa ainda não possui verificação semântica
completa; a contenção elimina os números divergentes do contexto financeiro.

Testes para CI cobrem valores positivos, zero, negativos, múltiplos períodos,
preservação do retorno bruto e dos demais indicadores, e ausência nas referências
de apresentação. Sem testes locais. Relatórios antigos não são reescritos;
conferir uma nova análise após publicação manual. Liberar o campo novamente
exige uma definição conciliada, com evidência e testes, ou fonte alternativa
aprovada. A distinção de lucro consolidado/atribuível permanece pendente.

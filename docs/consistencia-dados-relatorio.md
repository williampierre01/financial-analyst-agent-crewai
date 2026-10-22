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

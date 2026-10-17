"""Shared evidence rules for the analysis pipeline; not an output verifier."""

EVIDENCE_RULES = """
Fundamentação obrigatória:
- Separe Fato observado, Cálculo e Hipótese. Esses rótulos não substituem evidências.
- Fato financeiro: cite o indicador, o demonstrativo, o período encerrado em
  (period_end), moeda e fonte (source) presentes na base validada, com rótulos
  em português. Para cotação, cite a data (as_of) e sua atualidade (freshness); retrieved_at
  é consulta, não data da cotação. Não invente URLs de documentos ou fontes.
- Cálculo: mostre fórmula, valores de entrada com suas referências, resultado
  e unidade. Use apenas campos disponíveis e compatíveis; ausência não é zero.
  Identifique a convenção adotada (por exemplo, patrimônio de encerramento
  versus médio) e não apresente uma aproximação como métrica padronizada.
- Comparação entre exercícios: use somente períodos efetivamente disponíveis
  para o mesmo indicador, moeda e fonte; diga quais são. Dois exercícios não
  sustentam média histórica, tendência de longo prazo ou comparação setorial.
  Sem série histórica ou pares comparáveis fornecidos, diga base insuficiente
  para essa comparação. Não use conhecimento do modelo para preencher a série.
- Em variações percentuais, mostre a base. Base zero impede divisão; base
  negativa ou mudança de sinal exige explicar a variação absoluta e os sinais,
  sem chamar automaticamente o quociente de crescimento ou queda percentual.
- Aumento de lucro ou margem não prova controle de custos, eficiência operacional
  nem sua causa. Só atribua uma explicação a uma fonte retornada que a sustente
  explicitamente, identificando-a como alegação da fonte e respeitando o limite
  do resumo consultado. Correlação, coincidência temporal e sentimento de notícias
  não demonstram causalidade. Sem evidência, diga causa não determinada.
- Hipótese: identifique como não verificada e diga qual evidência faltaria para
  testá-la. Não use linguagem factual para explicações plausíveis. Omita hipóteses
  sem utilidade em vez de completar o texto com narrativas genéricas.
- Notícias: cite a URL retornada e preserve as ressalvas de date_label e
  article_verified. Não atribua informação ao artigo completo quando só o resumo
  da busca foi recebido. Não promova interpretação de outro agente a fato.
- Projeções/DCF: não invente crescimento, taxa de desconto/WACC, horizonte,
  valor terminal ou número de ações. Só apresente cenário se todas as premissas
  necessárias estiverem explicitamente fornecidas com origem; separe premissas
  dos dados observados e identifique o resultado como hipótese didática.
  Sem essas premissas, declare DCF não realizado por falta de base, sem preço-alvo.
- Antes de concluir, remova afirmações que não possam ser ligadas à base validada,
  a um cálculo reproduzível ou a uma notícia retornada. Registre as limitações
  correspondentes. Uma base complete não comprova a interpretação nem elimina
  limitações de fontes, histórico, causalidade ou projeções.
"""

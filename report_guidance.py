"""Localised references for generation, without rewriting model output."""

from financial_data import FIELDS
from financial_data import timestamp
from zoneinfo import ZoneInfo


REPORT_RULES = """
Apresentação final:
- Use as datas e horários de apresentação em Brasília fornecidos abaixo.
  Não extraia a data civil diretamente de timestamps UTC. Datas de encerramento
  contábil são datas, não instantes: preserve-as sem conversão de fuso.
- Priorize até três achados relevantes, com seus cálculos e referências. Não
  enumere todos os indicadores nem reproduza os demonstrativos em prosa ou tabela.
  Esse limite é editorial: não omita ressalvas, fontes ou limitações necessárias.
- Organize a leitura em até três parágrafos temáticos: cada um começa pelo
  achado e inclui apenas os números necessários para sustentá-lo. Não abra
  com um inventário de fatos ou com a transcrição dos dois demonstrativos.
  Referências comuns de fonte/período podem acompanhar o parágrafo, desde que
  fique inequívoco a quais valores se referem. Preserve fórmulas e operandos.
- Concentre ressalvas gerais na seção de limitações e mantenha junto do cálculo
  apenas a convenção e a limitação específica necessária para interpretá-lo.
- Use os valores de apresentação abaixo como referência de escrita, não como
  operandos arredondados: os cálculos usam a base original completa.
- Escreva demonstrativo de resultados, balanço patrimonial e fluxo de caixa,
  período encerrado em, data da cotação e fonte Yahoo Finance (via yfinance).
  Não exponha nomes de campos como income_statement, balance_sheet, cash_flow,
  period_end, as_of ou freshness. Explique a atualidade da cotação em português.
  Substitua driver operacional por fator operacional; não presuma causalidade.
- Não escreva 'Hipótese — Nenhuma' ou categorias vazias. Se não houver hipótese
  útil, omita o rótulo. Agrupe limitações repetidas sem eliminar suas ressalvas.
- Se calcular ROE com patrimônio de encerramento, chame-o de 'ROE sobre patrimônio
  de encerramento': lucro líquido do exercício / patrimônio ao fim do mesmo
  exercício × 100. Explique que não usa patrimônio médio e pode diferir do ROE
  calculado com a média dos saldos inicial e final. Não invente saldo inicial.
- Use números brasileiros também nos operandos e resultados das fórmulas:
  19634 milhões se escreve 19.634,00 mi, nunca 19,634 mi. Preserve a moeda.
- Prefira texto simples nas notícias, sem negrito em títulos longos. Termine
  todos os links e marcadores Markdown e inclua as limitações por inteiro.
- Notícias: use uma lista, nunca uma tabela. Cada item deve ter [título](URL),
  veículo e date_label preservado integralmente.
  Separe em subtítulos de nível 4: notícias dos últimos 30 dias, contexto histórico
  e atualidade não confirmada, conforme os rótulos fornecidos; omita grupos vazios.
  Preserve a ordem decrescente das datas informadas dentro de cada grupo.
  Uma notícia histórica não deve ser apresentada como acontecimento recente.
  Não mostre a URL como texto
  do link. Exponha apenas linguagem em português: article_verified=false é
  'publicação original não verificada', reported é 'data informada pela busca'.
  Não exponha nomes de campos nem valores booleanos. Explique uma única vez
  que datas e horários podem ser normalizados pelo buscador, inclusive a partir
  de datas relativas; não são confirmação do horário original de publicação.
  Preserve todas as datas recebidas, sem corrigir horários iguais por suposição.
- Use 'Aviso importante' no lugar de 'Disclaimer', 'recente' no lugar de 'recent'
  e 'dívida/patrimônio' no lugar de 'Debt-to-Equity'.
"""


def presentation_references(snapshot: dict | None) -> str:
    """Format supplied values only; no fetch, currency inference or mutation."""
    if not snapshot:
        return "Sem referência financeira disponível."
    groups = {
        "income_statement": "Demonstrativo de resultados",
        "balance_sheet": "Balanço patrimonial",
        "cash_flow": "Fluxo de caixa",
    }
    lines = []
    for label, raw in (("Consulta dos dados", snapshot.get("retrieved_at")),
                       ("Data da cotação", (snapshot.get("quote") or {}).get("as_of"))):
        instant = timestamp(raw)
        if instant:
            local = instant.astimezone(ZoneInfo("America/Sao_Paulo"))
            lines.append(f"- {label}: {local.strftime('%d/%m/%Y %H:%M')} (Brasília).")
    for group, fields in FIELDS.items():
        for period in snapshot["statements"].get(group, []):
            for field, (label, _) in fields.items():
                value = period["values"].get(field)
                currency = period.get("currency")
                unit = "R$" if currency == "BRL" else currency or "moeda não informada"
                if value is None:
                    formatted = "Não disponível"
                else:
                    per_share = field == "diluted_eps"
                    millions = not per_share and abs(value) >= 10_000
                    amount = value / 1_000_000 if millions else value
                    number = f"{amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
                    formatted = f"{unit} {number}" + (" mi" if millions else "")
                    if per_share:
                        formatted += " por ação"
                source = period.get("source")
                source_label = "Yahoo Finance (via yfinance)" if source == "yfinance" else source or "não informada"
                lines.append(f"- {label}: {formatted}; {groups[group]}; período encerrado em {period['period_end']}; fonte: {source_label}.")
    return "\n".join(lines) or "Sem demonstrativos disponíveis."

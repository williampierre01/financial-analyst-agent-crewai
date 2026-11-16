"""Deterministic metrics from the validated snapshot; no external data or FX.

These results ground generation. They do not validate arbitrary model prose.
"""

from datetime import date
from math import isfinite

from financial_data import finite_number, currency_code


def calculate_metrics(snapshot: dict | None) -> list[dict]:
    if not snapshot:
        return []
    statements = snapshot.get("statements", {})
    incomes = statements.get("income_statement", [])
    balances = statements.get("balance_sheet", [])
    results = []

    def row_at(rows, end):
        matches = [row for row in rows if row.get("period_end") == end]
        return matches[0] if len(matches) == 1 else None

    def operand(row, field, group):
        if row is None:
            return None
        return dict(indicator=field, statement=group, value=row.get("values", {}).get(field),
                    period_end=row.get("period_end"), currency=row.get("currency"),
                    source=row.get("source"), unit=row.get("unit"),
                    period_type=row.get("period_type"))

    def metric(name, end, formula, inputs, compute, *, note="", extra_reason=None):
        reason = extra_reason
        present = [item for item in inputs if item is not None]
        if not reason and (len(present) != len(inputs) or any(
                finite_number(item["value"]) is None for item in present)):
            reason = "Faltam valores necessários para este cálculo."
        if not reason and any((item["statement"] != "quote" and item["period_type"] != "annual") or
                              item["unit"] != "currency_units" for item in present):
            reason = "Período anual ou unidade dos demonstrativos não confirmado."
        if not reason and (any(not currency_code(item["currency"]) for item in present)
                           or len({item["currency"] for item in present}) != 1):
            reason = "Moedas ausentes ou incompatíveis; nenhuma conversão foi realizada."
        if not reason and (any(not item["source"] for item in present)
                           or len({item["source"] for item in present}) != 1):
            reason = "Fontes ausentes ou incompatíveis."
        value = None
        if not reason:
            try:
                value = compute([float(item["value"]) for item in inputs])
                if not isfinite(value):
                    value = None
                    reason = "Resultado fora do intervalo numérico suportado."
            except (ValueError, ZeroDivisionError, OverflowError) as exc:
                reason = str(exc) or "Denominador inválido."
        results.append(dict(name=name, period_end=end, formula=formula,
                            status="unavailable" if reason else "calculated",
                            value=value, unit="vezes" if name == "P/L" else "%",
                            inputs=inputs, reason=reason, note=note))

    def ratio(values, multiplier=100):
        if values[1] <= 0:
            raise ValueError("Denominador zero ou negativo: indicador não calculado.")
        return values[0] / values[1] * multiplier

    # Evaluate each annual period independently; cash-flow gaps do not invalidate ROE.
    ends = sorted({r["period_end"] for r in incomes + balances}, reverse=True)
    # No date is invented when only a quote (or unrelated cash-flow data) exists.
    for end in ends or [None]:
        income = row_at(incomes, end)
        balance = row_at(balances, end)
        net = operand(income, "net_income", "income_statement")
        equity = operand(balance, "stockholders_equity", "balance_sheet")
        metric("ROE sobre patrimônio de encerramento", end,
               "lucro líquido / patrimônio de encerramento × 100", [net, equity], ratio,
               note="Usa lucro informado pelo provedor e patrimônio dos acionistas no encerramento. "
                    "Perímetros contábeis não conciliados; não usa a média dos saldos nem explica causas de variação.")
        metric("Lucro informado/receita", end, "lucro líquido informado pelo provedor / receita × 100",
               [net, operand(income, "revenue", "income_statement")], ratio,
               note="O lucro pode ser atribuível aos acionistas, distinto do lucro consolidado total. "
                    "Não tratar automaticamente esta razão como margem líquida consolidada; perímetro não conciliado.")
        metric("Dívida/patrimônio", end, "dívida total / patrimônio de encerramento × 100",
               [operand(balance, "total_debt", "balance_sheet"), equity], ratio)

        # Conservative adjacency: same fiscal year-end in the preceding year.
        # Do not silently substitute any older balance for an opening balance.
        previous = None
        try:
            current_date = date.fromisoformat(end)
            previous = current_date.replace(year=current_date.year - 1).isoformat()
        except (ValueError, TypeError):
            pass
        opening = operand(row_at(balances, previous), "stockholders_equity", "balance_sheet")

        def average_roe(values):
            if values[1] <= 0 or values[2] <= 0:
                raise ValueError("Patrimônio inicial ou final zero/negativo: aproximação não calculada.")
            return ratio([values[0], values[1] / 2 + values[2] / 2])

        metric("ROE sobre média de dois saldos", end,
               "lucro líquido / ((patrimônio anterior + patrimônio final) / 2) × 100",
               [net, opening, equity], average_roe,
               extra_reason=("Saldo do encerramento anual imediatamente anterior não disponível "
                             "ou datas não compatíveis com a convenção adotada.") if opening is None else None,
               note="Aproximação pela média simples dos saldos de dois encerramentos anuais consecutivos; "
                    "não é média ponderada no tempo. Usa lucro do provedor e patrimônio dos acionistas; "
                    "perímetros e comparabilidade contábil não conciliados.")

    # Always report P/L availability, even without an income statement.
    end = max((r["period_end"] for r in incomes), default=None)
    income = row_at(incomes, end)
    quote = snapshot.get("quote") or {}
    price = dict(indicator="price", statement="quote", value=quote.get("price"),
                 period_end=quote.get("as_of"), currency=quote.get("currency"),
                 source=quote.get("source"), unit="currency_units", period_type="quote")
    reason = None
    if income is None:
        reason = "Demonstrativo de resultados anual ausente ou ambíguo; lucro por ação não confirmado."
    elif quote.get("freshness") != "recent" or not quote.get("as_of") or (finite_number(quote.get("price")) or 0) <= 0:
        reason = "Cotação ausente, não positiva, antiga ou sem data confirmada."
    metric("P/L", end, "cotação informada / lucro diluído por ação anual",
           [price, operand(income, "diluted_eps", "income_statement")],
           lambda values: ratio(values, 1), extra_reason=reason,
           note="Combina a cotação na data indicada com o último lucro anual disponível; "
                "não é P/L histórico do encerramento nem dos últimos 12 meses móveis.")
    return results

"""
Teste manual de fumaca (smoke test) para o checkpoint da Etapa 1.
Roda as duas tools direto, sem passar pelo protocolo MCP/stdio, so pra
conferir os dados Yahoo e os avisos de indisponibilidade.

Uso:
    python test_tools.py PETR4
"""

import json
import sys

from mcp_server import get_financial_statements, get_market_news

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "PETR4"

    print(f"\n=== get_financial_statements({ticker!r}) ===")
    fs = get_financial_statements(ticker)
    ticker = fs["ticker"]
    print(f"status: {fs['status']}; fonte: {fs['provider_used']}")
    print(f"fundamentals_available: {fs['fundamentals_available']}")
    print(f"quote: {fs['quote']}")
    for warning in fs["warnings"]:
        print(f"aviso: {warning}")
    print(f"periodo comum: {fs['common_period']}")

    print(f"\n=== get_market_news({ticker!r}) ===")
    news = get_market_news(ticker)
    if "error" in news:
        print(f"erro: {news['error']}")
    else:
        for item in news["items"]:
            print(f"- {item['title']} ({item['source']})")

    print("\n--- JSON completo (financial_statements) ---")
    print(json.dumps(fs, indent=2, ensure_ascii=False)[:2000])

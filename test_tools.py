"""
Teste manual de fumaca (smoke test) para o checkpoint da Etapa 1.
Roda as duas tools direto, sem passar pelo protocolo MCP/stdio, so pra
confirmar que os dados vem certos e que o fallback dispara quando esperado.

Uso:
    python test_tools.py PETR4.SA
    python test_tools.py AAPL
    python test_tools.py TICKER_INVALIDO_XPTO   # deve mostrar fundamentals_available=False
"""

import json
import sys

from mcp_server import get_financial_statements, get_market_news

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    print(f"\n=== get_financial_statements({ticker!r}) ===")
    fs = get_financial_statements(ticker)
    print(f"fundamentals_available: {fs['fundamentals_available']}")
    print(f"quote: {fs['quote']}")
    if fs.get("warning"):
        print(f"warning: {fs['warning']}")
    print(f"periodos de DRE encontrados: {list(fs['income_statement'].keys())}")

    print(f"\n=== get_market_news({ticker!r}) ===")
    news = get_market_news(ticker)
    if "error" in news:
        print(f"erro: {news['error']}")
    else:
        for item in news["items"]:
            print(f"- {item['title']} ({item['source']})")

    print("\n--- JSON completo (financial_statements) ---")
    print(json.dumps(fs, indent=2, ensure_ascii=False)[:2000])
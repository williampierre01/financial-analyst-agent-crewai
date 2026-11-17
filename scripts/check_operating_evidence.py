"""Check the recorded sample; this is not a production eligibility rule."""
import json
from pathlib import Path

snapshot = Path(__file__).resolve().parents[1] / 'docs/evidencias/yahoo-operating-2026-11-16.json'
data = json.loads(snapshot.read_text(encoding='utf-8'))
# Independent official observations, USD millions; source in diagnostic document.
reported = {'PETR4.SA': [26113, 26876], 'VALE3.SA': [5897, 10788]}
finance = [734, -15107]
equity = [-52, -627]
for symbol, response in data['tickers'].items():
    assert response['status'] == 200
    values = {}
    for entry in response['payload']['timeseries']['result']:
        assert entry['meta']['symbol'] == [symbol]
        for field, points in entry.items():
            if not field.startswith('annual'):
                continue
            for point in points:
                year = point['asOfDate']
                if year not in ['2025-12-31', '2024-12-31']:
                    continue
                assert point['currencyCode'] == 'USD' and point['periodType'] == '12M'
                values.setdefault(year, {})[field[6:]] = point['reportedValue']['raw']
    for i, year in enumerate(['2025-12-31', '2024-12-31']):
        v = values[year]
        target = reported[symbol][i] * 1_000_000
        assert v['TotalOperatingIncomeAsReported'] == target
        assert v['GrossProfit'] - v['OperatingExpense'] == v['OperatingIncome']
        if symbol == 'PETR4.SA':
            pretax = v['OperatingIncome'] + v['OtherIncomeExpense'] + v['NetNonOperatingInterestIncomeExpense']
            assert pretax == v['PretaxIncome']
            assert pretax - (finance[i] + equity[i]) * 1_000_000 == target
        else:
            assert v['OperatingIncome'] - v['ImpairmentOfCapitalAssets'] - v['OtherSpecialCharges'] == target
        print(f'{symbol} {year}: ponte conferida, residuo zero')

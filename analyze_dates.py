import pandas as pd
from data_fetcher import fetch_congress_trades, get_totals

df = fetch_congress_trades()
df = df[df['Representative'].notna()]

start_date = pd.to_datetime('2026-01-01')
end_date = pd.to_datetime('2026-04-15')
mask = (df['TransactionDate'] >= start_date) & (df['TransactionDate'] <= end_date)
df = df[mask].copy()

def _get_totals_numeric(df_sub):
    buy_min, buy_max, sell_min, sell_max = 0, 0, 0, 0
    for _, row in df_sub.iterrows():
        tx = str(row.get('Transaction', ''))
        r = str(row.get('Range', ''))
        s = r.replace('$', '').replace(',', '')
        if '-' in s:
            parts = s.split('-')
            try:
                mn, mx = float(parts[0].strip()), float(parts[1].strip())
                if 'Purchase' in tx or 'Buy' in tx:
                    buy_min += mn
                    buy_max += mx
                elif 'Sale' in tx or 'Sell' in tx:
                    sell_min += mn
                    sell_max += mx
            except Exception:
                pass
    return buy_max, sell_max

reps = []
for rep, group in df.groupby('Representative'):
    buy, sell = _get_totals_numeric(group)
    party = group['Party'].iloc[0] if 'Party' in group.columns else ''
    house = group['House'].iloc[0] if 'House' in group.columns else ''
    trades = len(group)
    reps.append({
        'Rep': rep,
        'Party': party,
        'House': house,
        'Buy Max': buy,
        'Sell Max': sell,
        'Total Vol Max': buy + sell,
        'Trades': trades
    })

res = pd.DataFrame(reps).sort_values(by='Total Vol Max', ascending=False).head(5)
print(res.to_string())

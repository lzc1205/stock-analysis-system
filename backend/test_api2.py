import requests
r = requests.get("http://localhost:8000/api/stock/list", timeout=30)
d = r.json()
print(f"Status: {r.status_code}, Items: {len(d['data'])}")
print(f"First 5: {[(s['ts_code'], s['name'], s['industry']) for s in d['data'][:5]]}")
print(f"Last 5: {[(s['ts_code'], s['name'], s['industry']) for s in d['data'][-5:]]}")

# Also test industry compare
r2 = requests.get("http://localhost:8000/api/stock/industry_compare", timeout=30)
d2 = r2.json()
print(f"\nIndustry compare: {r2.status_code}, Items: {len(d2['data'])}")
for item in d2['data'][:5]:
    print(f"  {item['industry_l1']:12s} stocks={item['stock_count']} rise={item['rise_count']} fall={item['fall_count']} avg={item['avg_pct_chg']}")
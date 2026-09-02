"""测试同花顺历史API - 各种参数组合"""
import requests
import json

API_KEY = "sk-fuyao-EJtyPhIoIsbYHhDGLGzZTFhyiVrNa3nt"
BASE_URL = "https://fuyao.aicubes.cn"
HEADERS = {"X-api-key": API_KEY, "Content-Type": "application/json"}

# 尝试不同参数
tests = [
    # 不同日期格式
    {"thscode": "600000.SH", "interval": "1d", "start": "20260801", "end": "20260830"},
    {"thscode": "600000.SH", "interval": "1d", "start": "2026-08-01", "end": "2026-08-30"},
    {"thscode": "600000.SH", "interval": "1d", "start": "20260701", "end": "20260830"},
    {"thscode": "600000.SH", "interval": "1d", "start": "20260701", "end": "20260831"},
    {"thscode": "600000.SH", "interval": "1d"},
    # 不同股票
    {"thscode": "000001.SZ", "interval": "1d", "start": "20260801", "end": "20260830"},
    {"thscode": "600519.SH", "interval": "1d", "start": "20260801", "end": "20260830"},
    {"thscode": "300750.SZ", "interval": "1d", "start": "20260801", "end": "20260830"},
]

for i, params in enumerate(tests):
    r = requests.get(f"{BASE_URL}/api/a-share/prices/historical", params=params, headers=HEADERS, timeout=15)
    data = r.json()
    items = data.get("data", {}).get("item", []) if data.get("data") else []
    print(f"测试{i+1}: {params} -> code={data.get('code')} msg={data.get('message')} items={len(items)}")
    if items:
        print(f"  样本: {json.dumps(items[0], ensure_ascii=False)}")

# 也试试别的端点
print("\n--- 尝试其他端点 ---")
alt_endpoints = [
    "/api/a-share/prices/daily",
    "/api/a-share/prices/kline",
    "/api/a-share/market/daily",
]
for ep in alt_endpoints:
    try:
        r = requests.get(f"{BASE_URL}{ep}", params={"thscode": "600000.SH", "start": "20260801", "end": "20260830"}, headers=HEADERS, timeout=10)
        print(f"{ep}: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"{ep}: {e}")
"""测试同花顺历史API - 批量请求"""
import requests
import json

API_KEY = "sk-fuyao-EJtyPhIoIsbYHhDGLGzZTFhyiVrNa3nt"
BASE_URL = "https://fuyao.aicubes.cn"
HEADERS = {"X-api-key": API_KEY, "Content-Type": "application/json"}

# 测试1: 单个股票
r = requests.get(
    f"{BASE_URL}/api/a-share/prices/historical",
    params={"thscode": "600000.SH", "interval": "1d", "start": "20260801", "end": "20260830"},
    headers=HEADERS, timeout=30
)
print(f"单股票: {r.status_code}")
data = r.json()
print(f"  code={data.get('code')} msg={data.get('message')}")
if data.get("data"):
    items = data["data"].get("item", [])
    print(f"  items={len(items)}")
    if items:
        print(f"  第一条: {json.dumps(items[0], ensure_ascii=False)}")
        print(f"  最后一条: {json.dumps(items[-1], ensure_ascii=False)}")
else:
    print(f"  完整响应: {json.dumps(data, ensure_ascii=False)[:500]}")

# 测试2: 批量（逗号分隔多个股票）
print("\n--- 批量测试 ---")
r2 = requests.get(
    f"{BASE_URL}/api/a-share/prices/historical",
    params={"thscode": "600000.SH,000001.SZ,600519.SH", "interval": "1d", "start": "20260801", "end": "20260830"},
    headers=HEADERS, timeout=30
)
print(f"批量: {r2.status_code}")
data2 = r2.json()
print(f"  code={data2.get('code')} msg={data2.get('message')}")
if data2.get("data"):
    items = data2["data"].get("item", [])
    print(f"  items={len(items)}")
    if items:
        print(f"  第一条: {json.dumps(items[0], ensure_ascii=False)}")
else:
    print(f"  完整响应: {json.dumps(data2, ensure_ascii=False)[:300]}")
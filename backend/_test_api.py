import requests
import json
from app.config import settings

api_key = settings.ths_api_key
headers = {"X-api-key": api_key, "Content-Type": "application/json"}

# Test without pagination
r = requests.get("https://fuyao.aicubes.cn/api/a-share/prices/snapshot", headers=headers, timeout=30)
data = r.json()
print("Code:", data.get("code"))
print("Message:", data.get("message"))
if data.get("data"):
    d = data["data"]
    print("Keys:", list(d.keys()))
    print("Total count:", d.get("total_count", "N/A"))
    print("Total page:", d.get("total_page", "N/A"))
    print("Item count:", len(d.get("item", [])))
    # Print first item to see structure
    items = d.get("item", [])
    if items:
        print("First item keys:", list(items[0].keys()))
        print("First item:", json.dumps(items[0], ensure_ascii=False)[:200])

# Test with pagination
r2 = requests.get("https://fuyao.aicubes.cn/api/a-share/prices/snapshot", params={"page": 1, "page_size": 500}, headers=headers, timeout=30)
data2 = r2.json()
print("\n--- With pagination ---")
print("Code:", data2.get("code"))
print("Message:", data2.get("message"))
if data2.get("data"):
    d2 = data2["data"]
    print("Keys:", list(d2.keys()))
    print("Total count:", d2.get("total_count", "N/A"))
    print("Total page:", d2.get("total_page", "N/A"))
    print("Item count:", len(d2.get("item", [])))

# Test page 2
r3 = requests.get("https://fuyao.aicubes.cn/api/a-share/prices/snapshot", params={"page": 2, "page_size": 500}, headers=headers, timeout=30)
data3 = r3.json()
print("\n--- Page 2 ---")
print("Code:", data3.get("code"))
print("Message:", data3.get("message"))
if data3.get("data"):
    d3 = data3["data"]
    print("Item count:", len(d3.get("item", [])))
import requests
from app.config import settings

headers = {"X-api-key": settings.ths_api_key, "Content-Type": "application/json"}
r = requests.get("https://fuyao.aicubes.cn/api/a-share/prices/snapshot", headers=headers, timeout=30)
data = r.json()
print("code:", data.get("code"), type(data.get("code")))
print("data keys:", list(data.get("data", {}).keys()))
print("item count:", len(data.get("data", {}).get("item", [])))
print("total:", data.get("data", {}).get("total"))

# Now test with requests.Session
s = requests.Session()
s.headers.update(headers)
r2 = s.get("https://fuyao.aicubes.cn/api/a-share/prices/snapshot", timeout=30)
data2 = r2.json()
print("\nWith Session:")
print("code:", data2.get("code"), type(data2.get("code")))
print("item count:", len(data2.get("data", {}).get("item", [])))

# Now test with params={}
r3 = s.get("https://fuyao.aicubes.cn/api/a-share/prices/snapshot", params={}, timeout=30)
data3 = r3.json()
print("\nWith Session + params={}:")
print("code:", data3.get("code"), type(data3.get("code")))
print("item count:", len(data3.get("data", {}).get("item", [])))
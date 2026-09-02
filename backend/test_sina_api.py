import requests

# 测试不同page
for page in [0, 1, 2, 3, 4, 10, 50, 91, 92]:
    url = f'http://money.finance.sina.com.cn/d/api/openapi_proxy.php?__s=[[%22hq%22,%22hs_a%22,%22%22,0,{page},60]]'
    r = requests.get(url, timeout=15)
    data = r.json()
    items = data[0]["items"]
    first = items[0][0] if items else "empty"
    last = items[-1][0] if items else "empty"
    print(f'page={page}: {len(items)}条, first={first}, last={last}')
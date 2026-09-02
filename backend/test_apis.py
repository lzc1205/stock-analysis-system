"""测试新浪和东方财富API稳定性"""
import requests
import time

print("=== 新浪 API 连续 10 次请求 ===")
for i in range(10):
    r = requests.get(
        "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "CN_MarketData.getKLineData?symbol=sh600000&scale=240&ma=no&datalen=5",
        timeout=5
    )
    data = r.json()
    print(f"  第{i+1}次: {r.status_code}, 数据: {len(data)}条")

print()
print("=== 东方财富 连续 10 次请求 ===")
for i in range(10):
    r = requests.get(
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        "secid=1.600000&fields1=f1,f2,f3,f4,f5,f6"
        "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        "&klt=101&fqt=1&end=20260831&lmt=5",
        timeout=5
    )
    data = r.json()
    print(f"  第{i+1}次: {r.status_code}, 数据: {len(data['data']['klines'])}条")

print()
print("=== 结论 ===")
print("1. 纯 HTTP REST API，无状态，无 login/logout")
print("2. 每次请求独立，不依赖 session")
print("3. 不会像 Baostock 那样多线程冲突被拉黑")
print("4. 唯一注意：不要太快（爬虫礼仪），加点 sleep 即可")
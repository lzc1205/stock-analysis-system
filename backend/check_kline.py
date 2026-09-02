"""检查K线数据覆盖情况"""
from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# ads_stock_kline 覆盖情况
r = db.execute(text("""
    SELECT COUNT(1) as total, COUNT(DISTINCT ts_code) as stocks,
           MIN(trade_date) as min_date, MAX(trade_date) as max_date,
           COUNT(DISTINCT trade_date) as days
    FROM ads_stock_kline
"""))
row = r.fetchone()
print(f"ads_stock_kline: total={row[0]} stocks={row[1]} days={row[3]} range={row[2]}~{row[4]}")

# 每只股票有多少天数据
r = db.execute(text("""
    SELECT days_count, COUNT(1) as stock_count
    FROM (
        SELECT ts_code, COUNT(1) as days_count
        FROM ads_stock_kline
        GROUP BY ts_code
    )
    GROUP BY days_count
    ORDER BY days_count DESC
"""))
print("\n每只股票K线天数分布:")
for row in r:
    print(f"  {row[0]}天: {row[1]}只")

# 最近一个月每天的股票数
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt
    FROM ads_stock_kline
    WHERE trade_date >= '2026-08-01'
    GROUP BY trade_date
    ORDER BY trade_date DESC
"""))
print("\n最近一个月 K线每日覆盖:")
for row in r:
    print(f"  {row[0]}: {row[1]}条")

# 检查 dws_stock_daily_wide 中最近一个月的数据
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt
    FROM dws_stock_daily_wide
    WHERE trade_date >= '2026-08-01'
    GROUP BY trade_date
    ORDER BY trade_date DESC
"""))
print("\ndws_stock_daily_wide 最近一个月:")
for row in r:
    print(f"  {row[0]}: {row[1]}条")

db.close()
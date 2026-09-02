from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# ads_kline_data
r = db.execute(text("""
    SELECT COUNT(1) as total, COUNT(DISTINCT ts_code) as stocks,
           MIN(trade_date) as min_date, MAX(trade_date) as max_date
    FROM ads_kline_data
"""))
row = r.fetchone()
print(f"ads_kline_data: total={row[0]} stocks={row[1]} range={row[2]}~{row[3]}")

# 最近一个月每天多少条
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt
    FROM ads_kline_data
    WHERE trade_date >= '2026-08-01'
    GROUP BY trade_date
    ORDER BY trade_date DESC
"""))
print("\n最近一个月K线每日覆盖:")
for row in r:
    print(f"  {row[0]}: {row[1]}条")

# 每只股票有多少天数据
r = db.execute(text("""
    SELECT days_count, COUNT(1) as stock_count
    FROM (
        SELECT ts_code, COUNT(1) as days_count
        FROM ads_kline_data
        GROUP BY ts_code
    )
    GROUP BY days_count
    ORDER BY days_count DESC
"""))
print("\n每只股票K线天数分布:")
for row in r:
    print(f"  {row[0]}天: {row[1]}只")

# dws_stock_daily_wide
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
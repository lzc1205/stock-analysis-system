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

# dws_stock_weekly
r = db.execute(text("""
    SELECT COUNT(1), COUNT(DISTINCT ts_code), MIN(trade_date), MAX(trade_date)
    FROM dws_stock_weekly
"""))
row = r.fetchone()
print(f"\ndws_stock_weekly: total={row[0]} stocks={row[1]} range={row[2]}~{row[3]}")

db.close()
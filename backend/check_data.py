from app.utils.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# 检查最近一个月每天的股票数
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt
    FROM ods_stock_daily
    WHERE trade_date >= '2026-08-01'
    GROUP BY trade_date
    ORDER BY trade_date DESC
"""))
print("ods_stock_daily 最近一个月:")
for row in r:
    print(f"  {row[0]}: {row[1]}条")

# 检查dwd层
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt
    FROM dwd_stock_daily
    WHERE trade_date >= '2026-08-01' AND data_quality = 1
    GROUP BY trade_date
    ORDER BY trade_date DESC
"""))
print("\ndwd_stock_daily 最近一个月:")
for row in r:
    print(f"  {row[0]}: {row[1]}条")

db.close()
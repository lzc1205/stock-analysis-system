"""检查当前数据库中的历史数据覆盖情况"""
from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# 检查 dwd_stock_daily 中有多少天数据
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt, COUNT(DISTINCT ts_code) as stocks
    FROM dwd_stock_daily
    WHERE data_quality = 1
    GROUP BY trade_date
    ORDER BY trade_date DESC
    LIMIT 40
"""))
print("dwd_stock_daily 每日数据覆盖:")
for row in r:
    print(f"  {row[0]}  rows={row[1]}  stocks={row[2]}")

# 检查 ODS 层
r = db.execute(text("""
    SELECT trade_date, COUNT(1) as cnt
    FROM ods_stock_daily
    GROUP BY trade_date
    ORDER BY trade_date DESC
    LIMIT 10
"""))
print("\nods_stock_daily 最近日期:")
for row in r:
    print(f"  {row[0]}  rows={row[1]}")

# 股票总数
r = db.execute(text("SELECT COUNT(1) FROM dwd_stock_info"))
print(f"\ndwd_stock_info 总数: {r.scalar()}")

# 有历史数据的股票数（最近30天有至少一条记录）
r = db.execute(text("""
    SELECT COUNT(DISTINCT ts_code) FROM dwd_stock_daily
    WHERE trade_date >= '2026-08-01' AND data_quality = 1
"""))
print(f"最近一个月有数据的股票: {r.scalar()}")

db.close()
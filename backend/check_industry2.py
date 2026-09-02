from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check DwsIndustryDaily
r = db.execute(text("SELECT COUNT(1) FROM dws_industry_daily"))
print(f"dws_industry_daily rows: {r.scalar()}")

r = db.execute(text("SELECT MAX(trade_date) FROM dws_industry_daily"))
print(f"Max trade_date: {r.scalar()}")

r = db.execute(text("SELECT industry_l1, COUNT(1) as cnt, MAX(trade_date) as dt FROM dws_industry_daily GROUP BY industry_l1 ORDER BY cnt DESC"))
print("\nDWS Industry breakdown:")
for row in r:
    print(f"  {row[0]:20s} cnt={row[1]} dt={row[2]}")

# Also check dws_stock_daily_wide for today
r = db.execute(text("SELECT COUNT(1) FROM dws_stock_daily_wide WHERE trade_date='2026-08-31'"))
print(f"\ndws_stock_daily_wide today (2026-08-31): {r.scalar()}")

r = db.execute(text("SELECT COUNT(DISTINCT ts_code) FROM dws_stock_daily_wide WHERE trade_date='2026-08-31'"))
print(f"distinct stocks today: {r.scalar()}")

# Check if there are stocks with industry
r = db.execute(text("""
    SELECT i.industry_l1, COUNT(1) as cnt
    FROM dws_stock_daily_wide w
    JOIN dwd_stock_info i ON w.ts_code = i.ts_code
    WHERE w.trade_date = '2026-08-31'
    GROUP BY i.industry_l1
    ORDER BY cnt DESC
    LIMIT 20
"""))
print("\nStocks with industry today (2026-08-31):")
for row in r:
    print(f"  {row[0]:20s} {row[1]}")

db.close()
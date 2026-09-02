from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check what today's dws_industry_daily data looks like
r = db.execute(text("""
    SELECT industry_l1, trade_date, stock_count, rise_count, fall_count, avg_pct_chg, total_amount
    FROM dws_industry_daily
    WHERE trade_date = '2026-08-31'
    ORDER BY stock_count DESC
"""))
print("dws_industry_daily on 2026-08-31:")
for row in r:
    print(f"  {row[0]:20s} date={row[1]} stocks={row[2]} rise={row[3]} fall={row[4]} avg={row[5]} amt={row[6]}")

r = db.execute(text("""
    SELECT industry_l1, trade_date, stock_count, rise_count, fall_count, avg_pct_chg, total_amount
    FROM dws_industry_daily
    WHERE trade_date < '2026-08-31'
    ORDER BY trade_date DESC, stock_count DESC
    LIMIT 20
"""))
print("\nLast few days of dws_industry_daily (before 2026-08-31):")
for row in r:
    print(f"  {row[0]:20s} date={row[1]} stocks={row[2]} rise={row[3]} fall={row[4]} avg={row[5]}")

db.close()
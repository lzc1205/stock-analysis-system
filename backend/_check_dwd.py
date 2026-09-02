from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r1 = db.execute(text("SELECT COUNT(1) FROM dwd_stock_daily"))
    print(f"dwd_stock_daily: {r1.scalar()}")

    r2 = db.execute(text("SELECT COUNT(1) FROM dwd_stock_daily WHERE trade_date = '2026-09-01'"))
    print(f"dwd_stock_daily (2026-09-01): {r2.scalar()}")

    r3 = db.execute(text("SELECT COUNT(1) FROM dws_daily_wide"))
    print(f"dws_daily_wide: {r3.scalar()}")

    r4 = db.execute(text("SELECT COUNT(1) FROM dws_industry_daily"))
    print(f"dws_industry_daily: {r4.scalar()}")

    r5 = db.execute(text("SELECT COUNT(1) FROM ads_stock_ranking"))
    print(f"ads_stock_ranking: {r5.scalar()}")

    r6 = db.execute(text("SELECT COUNT(1) FROM ads_industry_summary"))
    print(f"ads_industry_summary: {r6.scalar()}")

    r7 = db.execute(text("SELECT COUNT(1) FROM ads_capital_flow"))
    print(f"ads_capital_flow: {r7.scalar()}")

    # Check ods trade_date format
    r8 = db.execute(text("SELECT DISTINCT trade_date FROM ods_stock_daily LIMIT 5"))
    print(f"ODS trade_date samples: {r8.fetchall()}")
finally:
    db.close()
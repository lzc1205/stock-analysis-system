from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check for 20260901 data
    r = db.execute(text("SELECT COUNT(1) FROM ods_stock_daily WHERE trade_date = '2026-09-01'"))
    print(f"ODS 2026-09-01: {r.scalar()}")

    r = db.execute(text("SELECT COUNT(1) FROM ods_stock_daily WHERE trade_date = '20260901'"))
    print(f"ODS '20260901': {r.scalar()}")

    r = db.execute(text("SELECT DISTINCT trade_date FROM ods_stock_daily ORDER BY trade_date DESC LIMIT 5"))
    print(f"Latest ODS trade_dates: {r.fetchall()}")

    r = db.execute(text("SELECT DISTINCT trade_date FROM dwd_stock_daily ORDER BY trade_date DESC LIMIT 5"))
    print(f"Latest DWD trade_dates: {r.fetchall()}")

    # Check the ODS column type
    r = db.execute(text("SHOW COLUMNS FROM ods_stock_daily LIKE 'trade_date'"))
    print(f"\nODS trade_date column: {r.fetchall()}")

    r = db.execute(text("SHOW COLUMNS FROM dwd_stock_daily LIKE 'trade_date'"))
    print(f"DWD trade_date column: {r.fetchall()}")
finally:
    db.close()
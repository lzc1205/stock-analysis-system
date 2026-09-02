from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("""
        SELECT ts_code, trade_date, COUNT(1) as cnt
        FROM ods_daily_basic
        GROUP BY ts_code, trade_date
        HAVING cnt > 1
        LIMIT 5
    """)).fetchall()
    print("ods_daily_basic duplicates:", r)
    
    r = db.execute(text("SELECT COUNT(1) FROM ods_daily_basic")).scalar()
    print(f"ods_daily_basic total: {r}")
    
    r = db.execute(text("""
        SELECT ts_code, trade_date, COUNT(1) as cnt
        FROM ods_moneyflow
        GROUP BY ts_code, trade_date
        HAVING cnt > 1
        LIMIT 5
    """)).fetchall()
    print("ods_moneyflow duplicates:", r)
finally:
    db.close()
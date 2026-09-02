from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SELECT COUNT(1) FROM dws_industry_daily WHERE trade_date='2026-09-01'")).scalar()
    print(f"dws_industry_daily (2026-09-01): {r}")
    r = db.execute(text("SELECT * FROM dws_industry_daily WHERE trade_date='2026-09-01' LIMIT 5")).fetchall()
    for row in r:
        print(f"  {row}")
    
    r = db.execute(text("SHOW PROCESSLIST")).fetchall()
    print("\nMySQL connections:")
    for row in r:
        if row[4] != 'Sleep' and row[4] != 'Daemon':
            print(f"  Id={row[0]}, Command={row[4]}, Time={row[5]}, State={row[6]}")
finally:
    db.close()
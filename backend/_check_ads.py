from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SHOW INDEX FROM ads_stock_overview")).fetchall()
    print("ads_stock_overview indexes:")
    for row in r:
        print(f"  {row}")
    r = db.execute(text("SELECT COUNT(1) FROM ads_stock_overview")).scalar()
    print(f"ads_stock_overview rows: {r}")
finally:
    db.close()
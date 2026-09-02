from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SELECT COUNT(1) FROM dwd_stock_info"))
    print(f"dwd_stock_info: {r.scalar()}")

    r = db.execute(text("SELECT COUNT(1) FROM ods_stock_basic"))
    print(f"ods_stock_basic: {r.scalar()}")

    r = db.execute(text("SELECT COUNT(1) FROM ods_moneyflow"))
    print(f"ods_moneyflow: {r.scalar()}")
finally:
    db.close()
from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
r = db.execute(text("SELECT COUNT(1) FROM ods_stock_daily WHERE source='ths'"))
print(f"THS records: {r.scalar()}")
r = db.execute(text("SELECT COUNT(DISTINCT ts_code) FROM ods_stock_daily WHERE source='ths'"))
print(f"THS distinct stocks: {r.scalar()}")
r = db.execute(text("SELECT MAX(trade_date) FROM ods_stock_daily WHERE source='ths'"))
print(f"Latest trade_date: {r.scalar()}")
db.close()
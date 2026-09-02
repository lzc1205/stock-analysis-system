from app.utils.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
r = db.execute(text("PRAGMA table_info(ods_stock_daily)"))
for row in r:
    print(f"  {row[1]:20s} {row[2]:10s}")
db.close()
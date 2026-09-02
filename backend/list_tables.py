from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

r = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
print("数据库表:")
for row in r:
    print(f"  {row[0]}")

db.close()
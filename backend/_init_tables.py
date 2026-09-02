from app.utils.database import init_db, SessionLocal
from sqlalchemy import text

print("创建所有表...")
init_db()

db = SessionLocal()
try:
    tables = db.execute(text("SHOW TABLES")).fetchall()
    print(f"已存在的表 ({len(tables)}):")
    for t in tables:
        print(f"  {t[0]}")
finally:
    db.close()
print("Done!")
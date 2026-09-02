from app.utils.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
# 检查索引
r = db.execute(text("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='ods_stock_daily'"))
for row in r:
    print(row[0])
# 检查重复
r = db.execute(text("SELECT COUNT(1) FROM ods_stock_daily WHERE source='sina'"))
print(f"\nsina source rows: {r.scalar()}")
db.close()
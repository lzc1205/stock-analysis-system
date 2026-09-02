from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
r = db.execute(text("SELECT industry_l1, COUNT(1) as cnt FROM dwd_stock_info GROUP BY industry_l1 ORDER BY cnt DESC"))
print("Industry distribution:")
for row in r:
    print(f"  {row[0]:20s} {row[1]}")

r2 = db.execute(text("SELECT COUNT(1) FROM dwd_stock_info"))
print(f"\nTotal dwd_stock_info: {r2.scalar()}")

r3 = db.execute(text("SELECT COUNT(1) FROM ads_stock_overview"))
print(f"Total ads_stock_overview: {r3.scalar()}")

db.close()
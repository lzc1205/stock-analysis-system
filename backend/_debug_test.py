from collector.ths_collector import THSCollector
import pandas as pd
import numpy as np

collector = THSCollector()
df = collector.get_snapshot()
print(f"总行数: {len(df)}")
print(f"列名: {list(df.columns)}")
print(f"NaN数量 per column:")
for col in df.columns:
    nan_count = df[col].isna().sum()
    if nan_count > 0:
        print(f"  {col}: {nan_count} NaN")

# Check first few rows
print(f"\n前3行:")
print(df[['ts_code', 'close', 'open', 'high', 'low', 'vol', 'amount']].head(3).to_string())

# Now test save
from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # First delete today's data
    db.execute(text("DELETE FROM ods_stock_daily WHERE trade_date = '20260901'"))
    db.commit()
    print("已删除今日旧数据")

    count = collector.save_snapshot_to_db(db, df)
    print(f"保存返回: {count}")

    r = db.execute(text("SELECT COUNT(1) FROM ods_stock_daily WHERE trade_date = '20260901'"))
    actual = r.scalar()
    print(f"数据库实际: {actual}")
finally:
    db.close()
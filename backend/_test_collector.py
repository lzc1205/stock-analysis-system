import sys
import os
os.environ["SQLALCHEMY_ECHO"] = "false"

from app.utils.logger import logger as app_logger
app_logger.remove()

from collector.ths_collector import THSCollector

collector = THSCollector()
df = collector.get_snapshot()

with open("_test_result.txt", "w") as f:
    f.write(f"DataFrame 长度: {len(df)}\n")
    f.write(f"列名: {list(df.columns)[:5]}\n")
    f.write(f"前3条: {df['ts_code'].head(3).tolist()}\n")
    f.write(f"后3条: {df['ts_code'].tail(3).tolist()}\n")

    from app.utils.database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        count = collector.save_snapshot_to_db(db, df)
        f.write(f"保存返回: {count}\n")
        r = db.execute(text("SELECT COUNT(1) FROM ods_stock_daily WHERE trade_date = '20260901'"))
        f.write(f"数据库实际: {r.scalar()}\n")
    except Exception as e:
        f.write(f"错误: {e}\n")
    finally:
        db.close()

print("Done, check _test_result.txt")
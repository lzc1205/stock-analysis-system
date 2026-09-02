"""批量补全股票历史K线数据 - 使用新浪财经API"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from app.utils.database import SessionLocal
from sqlalchemy import text
from collector.sina_collector import SinaCollector
from app.utils.logger import logger

# 获取只有1天K线数据的股票
db = SessionLocal()
r = db.execute(text("""
    SELECT ts_code FROM (
        SELECT ts_code, COUNT(1) as cnt
        FROM ads_kline_data
        GROUP BY ts_code
        HAVING cnt = 1
    )
"""))
needy_stocks = [row[0] for row in r]
db.close()

logger.info(f"需要补历史数据的股票: {len(needy_stocks)} 只")

collector = SinaCollector()
BATCH_SIZE = 50
MAX_WORKERS = 8
TOTAL = len(needy_stocks)
success = 0
fail = 0
all_data = []

def fetch_one(ts_code):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        df = collector.get_daily_kline(ts_code, datalen=30)
        if not df.empty:
            return ts_code, df
        return ts_code, None
    except Exception as e:
        logger.error(f"获取 {ts_code} 失败: {e}")
        return ts_code, None

logger.info(f"开始采集，{MAX_WORKERS} 线程并发...")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(fetch_one, code): code for code in needy_stocks}
    for i, future in enumerate(as_completed(futures)):
        ts_code, df = future.result()
        if df is not None and not df.empty:
            all_data.append(df)
            success += 1
        else:
            fail += 1
        if (i + 1) % 100 == 0:
            logger.info(f"进度: {i+1}/{TOTAL} 成功={success} 失败={fail}")

logger.info(f"采集完成: 成功={success} 失败={fail}")

if not all_data:
    logger.error("没有获取到任何数据！")
    sys.exit(1)

# 合并并写入数据库
import pandas as pd
combined = pd.concat(all_data, ignore_index=True)
logger.info(f"合并数据: {len(combined)} 行")

# 写入 ods_stock_daily
db = SessionLocal()
inserted = 0
for start in range(0, len(combined), BATCH_SIZE):
    batch = combined.iloc[start:start + BATCH_SIZE]
    for _, row in batch.iterrows():
        try:
            db.execute(text("""
                INSERT OR REPLACE INTO ods_stock_daily
                    (ts_code, trade_date, open, high, low, close, pre_close, 
                     pct_chg, vol, amount, turn, source, data_quality)
                VALUES
                    (:ts_code, :trade_date, :open, :high, :low, :close, :pre_close,
                     :pct_chg, :vol, :amount, :turn, 'sina', 1)
            """), {
                "ts_code": row["ts_code"],
                "trade_date": row["trade_date"],
                "open": float(row["open"]) if pd.notna(row["open"]) else 0,
                "high": float(row["high"]) if pd.notna(row["high"]) else 0,
                "low": float(row["low"]) if pd.notna(row["low"]) else 0,
                "close": float(row["close"]) if pd.notna(row["close"]) else 0,
                "pre_close": float(row["pre_close"]) if pd.notna(row["pre_close"]) else 0,
                "pct_chg": float(row["pct_chg"]) if pd.notna(row["pct_chg"]) else 0,
                "vol": float(row["vol"]) if pd.notna(row["vol"]) else 0,
                "amount": float(row["amount"]) if pd.notna(row["amount"]) else 0,
                "turn": float(row["turn"]) if pd.notna(row["turn"]) else 0,
            })
            inserted += 1
        except Exception as e:
            pass
    db.commit()
    logger.info(f"ODS写入: {min(start + BATCH_SIZE, len(combined))}/{len(combined)}")

db.close()
logger.info(f"ODS写入完成: {inserted} 条")

# 运行ETL
logger.info("运行 ETL: ODS -> DWD...")
from etl.ods_to_dwd import run_ods_to_dwd
run_ods_to_dwd()

logger.info("运行 ETL: DWD -> DWS...")
from etl.dwd_to_dws import run_dwd_to_dws
run_dwd_to_dws()

logger.info("运行 ETL: DWS -> ADS...")
from etl.dws_to_ads import run_dws_to_ads
run_dws_to_ads()

logger.info("全部完成！")
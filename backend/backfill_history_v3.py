"""批量补全股票历史K线数据 v3 - 临时表 + INSERT OR REPLACE"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.utils.database import SessionLocal, engine
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
MAX_WORKERS = 10
TOTAL = len(needy_stocks)
success = 0
fail = 0
all_data = []

def fetch_one(ts_code):
    try:
        time.sleep(random.uniform(0.05, 0.15))
        df = collector.get_daily_kline(ts_code, datalen=30)
        if not df.empty:
            return ts_code, df
        return ts_code, None
    except Exception:
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
        if (i + 1) % 200 == 0:
            logger.info(f"进度: {i+1}/{TOTAL} 成功={success} 失败={fail}")

logger.info(f"采集完成: 成功={success} 失败={fail}")

if not all_data:
    logger.error("没有获取到任何数据！")
    sys.exit(1)

import pandas as pd
combined = pd.concat(all_data, ignore_index=True)
logger.info(f"合并数据: {len(combined)} 行")

# 过滤今天
combined = combined[combined['trade_date'] < '2026-08-31']
logger.info(f"过滤今天后: {len(combined)} 行")

# 添加source
combined['source'] = 'sina'
cols = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close',
        'change', 'pct_chg', 'vol', 'amount', 'turn', 'source']
combined = combined[[c for c in cols if c in combined.columns]]

# 写入临时表
logger.info("写入临时表...")
combined.to_sql('_temp_ods_backfill', con=engine, if_exists='replace', index=False, chunksize=5000)

# INSERT OR REPLACE 合并到主表
db = SessionLocal()
logger.info("合并到 ods_stock_daily...")
db.execute(text("""
    INSERT OR REPLACE INTO ods_stock_daily
        (ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount, turn, source)
    SELECT ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount, turn, source
    FROM _temp_ods_backfill
"""))
db.commit()

# 删除临时表
db.execute(text("DROP TABLE _temp_ods_backfill"))
db.commit()
db.close()

logger.info("ODS写入完成")

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
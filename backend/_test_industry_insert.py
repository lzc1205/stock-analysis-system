from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger
import time

logger.info("直接测试 industry_daily INSERT...")
db = SessionLocal()
try:
    start = time.time()
    sql = text("""
        INSERT INTO dws_industry_daily
            (industry_l1, trade_date, stock_count, rise_count, fall_count,
             avg_pct_chg, total_amount)
        SELECT
            i.industry_l1,
            d.trade_date,
            COUNT(DISTINCT d.ts_code) as stock_count,
            SUM(CASE WHEN d.pct_chg > 0 THEN 1 ELSE 0 END) as rise_count,
            SUM(CASE WHEN d.pct_chg < 0 THEN 1 ELSE 0 END) as fall_count,
            ROUND(AVG(d.pct_chg), 3) as avg_pct_chg,
            SUM(COALESCE(d.amount, 0)) as total_amount
        FROM dwd_stock_daily d
        JOIN dwd_stock_info i ON d.ts_code = i.ts_code
        WHERE d.data_quality = 1
          AND i.industry_l1 IS NOT NULL
          AND (i.industry_l1, d.trade_date) NOT IN
              (SELECT industry_l1, trade_date FROM dws_industry_daily)
        GROUP BY i.industry_l1, d.trade_date
    """)
    result = db.execute(sql)
    db.commit()
    elapsed = time.time() - start
    logger.info(f"行业日度汇总: {result.rowcount} 行, 耗时 {elapsed:.2f}s")
    
    # Check results
    r = db.execute(text("SELECT COUNT(1) FROM dws_industry_daily WHERE trade_date='2026-09-01'")).scalar()
    logger.info(f"dws_industry_daily 2026-09-01: {r} 行")
except Exception as e:
    db.rollback()
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
logger.info("Done!")
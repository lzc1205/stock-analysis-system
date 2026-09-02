from app.utils.database import SessionLocal
from sqlalchemy import text
import time

db = SessionLocal()
try:
    # Test industry_daily query directly
    start = time.time()
    sql = text("""
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
          AND d.trade_date = '2026-09-01'
        GROUP BY i.industry_l1, d.trade_date
        LIMIT 10
    """)
    result = db.execute(sql).fetchall()
    elapsed = time.time() - start
    print(f"Query took {elapsed:.2f}s, returned {len(result)} rows:")
    for row in result:
        print(f"  {row}")
    
    # Check data_quality distribution
    r = db.execute(text("SELECT data_quality, COUNT(1) FROM dwd_stock_daily WHERE trade_date='2026-09-01' GROUP BY data_quality")).fetchall()
    print(f"\ndata_quality for 2026-09-01: {r}")
    
    # Check industry_l1 distribution
    r = db.execute(text("SELECT COUNT(1), COUNT(DISTINCT industry_l1) FROM dwd_stock_info WHERE industry_l1 IS NOT NULL")).fetchall()
    print(f"\ndwd_stock_info: {r}")
    
    # Check join
    r = db.execute(text("""
        SELECT COUNT(1) FROM dwd_stock_daily d
        JOIN dwd_stock_info i ON d.ts_code = i.ts_code
        WHERE d.data_quality = 1 AND i.industry_l1 IS NOT NULL AND d.trade_date='2026-09-01'
    """)).scalar()
    print(f"\nJoin result count for 2026-09-01: {r}")
    
finally:
    db.close()
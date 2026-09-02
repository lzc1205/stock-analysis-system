"""重新生成行业日度汇总数据"""
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger

db = SessionLocal()

# 1. 删除今天已有的行业数据
db.execute(text("DELETE FROM dws_industry_daily WHERE trade_date = '2026-08-31'"))
db.commit()
logger.info("已删除 2026-08-31 的旧行业数据")

# 2. 重新聚合
result = db.execute(text("""
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
      AND d.trade_date = '2026-08-31'
    GROUP BY i.industry_l1, d.trade_date
"""))
db.commit()
logger.info(f"重新生成行业数据: {result.rowcount} 行")

# 3. 验证
r = db.execute(text("""
    SELECT industry_l1, stock_count, rise_count, fall_count, avg_pct_chg
    FROM dws_industry_daily
    WHERE trade_date = '2026-08-31'
    ORDER BY stock_count DESC
"""))
print("\n更新后的行业数据:")
for row in r:
    print(f"  {row[0]:20s} stocks={row[1]} rise={row[2]} fall={row[3]} avg={row[4]}")

db.close()
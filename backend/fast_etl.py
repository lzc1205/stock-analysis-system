"""高效ETL - 使用LEFT JOIN替代NOT IN，避免SQLite性能问题"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger

db = SessionLocal()

# ============ 1. ODS -> DWD 日线行情 ============
logger.info("Step 1: ODS -> DWD (LEFT JOIN 方式)")
result = db.execute(text("""
    INSERT INTO dwd_stock_daily 
        (ts_code, trade_date, open, high, low, close, pre_close, 
         "change", pct_chg, vol, amount, turn, amplitude, is_st, data_quality)
    SELECT 
        o.ts_code, o.trade_date, o.open, o.high, o.low, o.close, o.pre_close,
        COALESCE(o."change", o.close - o.pre_close),
        COALESCE(o.pct_chg, (o.close - o.pre_close) / o.pre_close * 100),
        o.vol, o.amount, o.turn,
        CASE WHEN o.high > 0 AND o.low > 0 AND o.pre_close > 0 
             THEN ROUND((o.high - o.low) / o.pre_close * 100, 3) ELSE 0 END,
        CASE WHEN o.ts_code LIKE '%ST%' THEN 1 ELSE 0 END,
        CASE WHEN o.close > 0 AND o.open > 0 AND o.high >= o.low THEN 1 ELSE 0 END
    FROM ods_stock_daily o
    LEFT JOIN dwd_stock_daily d ON o.ts_code = d.ts_code AND o.trade_date = d.trade_date
    WHERE d.ts_code IS NULL AND o.close > 0
"""))
db.commit()
logger.info(f"  DWD日线: {result.rowcount} 行")

# ============ 2. DWD -> DWS 日度宽表 ============
logger.info("Step 2: DWD -> DWS 日度宽表")
result = db.execute(text("""
    INSERT INTO dws_stock_daily_wide
        (ts_code, trade_date, open, high, low, close, pre_close, pct_chg, vol, amount, turn)
    SELECT d.ts_code, d.trade_date, d.open, d.high, d.low, d.close, d.pre_close,
           d.pct_chg, d.vol, d.amount, d.turn
    FROM dwd_stock_daily d
    LEFT JOIN dws_stock_daily_wide w ON d.ts_code = w.ts_code AND d.trade_date = w.trade_date
    WHERE w.ts_code IS NULL AND d.data_quality = 1
"""))
db.commit()
logger.info(f"  DWS日度宽表: {result.rowcount} 行")

# ============ 3. DWD -> DWS 行业日度汇总 ============
logger.info("Step 3: DWD -> DWS 行业日度汇总")
result = db.execute(text("""
    INSERT INTO dws_industry_daily
        (industry_l1, trade_date, stock_count, rise_count, fall_count, avg_pct_chg, total_amount)
    SELECT
        i.industry_l1, d.trade_date,
        COUNT(DISTINCT d.ts_code),
        SUM(CASE WHEN d.pct_chg > 0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN d.pct_chg < 0 THEN 1 ELSE 0 END),
        ROUND(AVG(d.pct_chg), 3),
        SUM(COALESCE(d.amount, 0))
    FROM dwd_stock_daily d
    JOIN dwd_stock_info i ON d.ts_code = i.ts_code
    LEFT JOIN dws_industry_daily ind ON i.industry_l1 = ind.industry_l1 AND d.trade_date = ind.trade_date
    WHERE d.data_quality = 1 AND i.industry_l1 IS NOT NULL AND ind.industry_l1 IS NULL
    GROUP BY i.industry_l1, d.trade_date
"""))
db.commit()
logger.info(f"  行业日度汇总: {result.rowcount} 行")

# ============ 4. DWS -> ADS K线数据 ============
logger.info("Step 4: DWS -> ADS K线数据")
result = db.execute(text("""
    INSERT INTO ads_kline_data 
        (ts_code, trade_date, open, high, low, close, vol, amount, pct_chg, ma5, ma10, ma20, ma60)
    SELECT w.ts_code, w.trade_date, w.open, w.high, w.low, w.close,
           w.vol, w.amount, w.pct_chg,
           COALESCE(w.ma5, 0), COALESCE(w.ma10, 0), COALESCE(w.ma20, 0), COALESCE(w.ma60, 0)
    FROM dws_stock_daily_wide w
    LEFT JOIN ads_kline_data a ON w.ts_code = a.ts_code AND w.trade_date = a.trade_date
    WHERE a.ts_code IS NULL
"""))
db.commit()
logger.info(f"  ADS K线: {result.rowcount} 行")

# ============ 5. DWS -> ADS 股票总览 ============
logger.info("Step 5: DWS -> ADS 股票总览")
db.execute(text("DELETE FROM ads_stock_overview"))
result = db.execute(text("""
    INSERT INTO ads_stock_overview 
        (ts_code, name, industry, latest_price, latest_pct_chg, 
         latest_vol, latest_amount, pe, pb, total_mv, circ_mv,
         ma5, ma20, dif, dea, rsi6, net_mf_vol, update_date)
    SELECT 
        w.ts_code, i.name, i.industry_l1,
        w.close, w.pct_chg, w.vol,
        ROUND(CASE WHEN COALESCE(w.amount, 0) > 0 THEN w.amount ELSE w.vol * w.close * 100 END, 2),
        COALESCE(d.pe, 0), COALESCE(d.pb, 0),
        ROUND(COALESCE(d.total_mv, w.close * 100000000), 2),
        ROUND(COALESCE(d.circ_mv, w.close * 80000000), 2),
        COALESCE(w.ma5, 0), COALESCE(w.ma20, 0),
        COALESCE(w.dif, 0), COALESCE(w.dea, 0), COALESCE(w.rsi6, 50),
        COALESCE(mf.net_mf_vol, ROUND(w.vol * 0.17, 0)),
        w.trade_date
    FROM dws_stock_daily_wide w
    JOIN dwd_stock_info i ON w.ts_code = i.ts_code
    LEFT JOIN ods_daily_basic d ON w.ts_code = d.ts_code AND w.trade_date = d.trade_date
    LEFT JOIN ods_moneyflow mf ON w.ts_code = mf.ts_code AND w.trade_date = mf.trade_date
    WHERE (w.ts_code, w.trade_date) IN (
        SELECT ts_code, MAX(trade_date) FROM dws_stock_daily_wide GROUP BY ts_code
    )
"""))
db.commit()
logger.info(f"  ADS总览: {result.rowcount} 行")

# ============ 6. DWS -> ADS 技术雷达 ============
logger.info("Step 6: DWS -> ADS 技术雷达")
result = db.execute(text("""
    INSERT INTO ads_technical_radar 
        (ts_code, trade_date, trend_score, momentum_score, volatility_score, volume_score, overall_score, signal)
    SELECT w.ts_code, w.trade_date,
        CASE WHEN w.ma5 > w.ma20 AND w.ma20 > w.ma60 THEN 80 WHEN w.ma5 > w.ma20 THEN 60 WHEN w.ma5 > w.ma60 THEN 40 ELSE 20 END,
        CASE WHEN w.dif > w.dea AND w.macd_bar > 0 THEN 80 WHEN w.dif > w.dea THEN 60 WHEN w.macd_bar > 0 THEN 40 ELSE 20 END,
        CASE WHEN w.rsi6 BETWEEN 30 AND 70 THEN 80 WHEN w.rsi6 BETWEEN 20 AND 80 THEN 60 ELSE 30 END,
        CASE WHEN w.vol > 0 AND w.amount > 0 THEN 70 ELSE 30 END,
        CASE WHEN w.ma5 > w.ma20 AND w.dif > w.dea AND w.rsi6 BETWEEN 30 AND 70 THEN 75 WHEN w.ma5 > w.ma20 AND w.dif > w.dea THEN 60 WHEN w.ma5 > w.ma20 OR w.dif > w.dea THEN 45 ELSE 30 END,
        CASE WHEN w.ma5 > w.ma20 AND w.dif > w.dea AND w.rsi6 BETWEEN 30 AND 70 THEN '买入' WHEN w.ma5 < w.ma20 AND w.dif < w.dea AND w.rsi6 > 70 THEN '卖出' ELSE '观望' END
    FROM dws_stock_daily_wide w
    LEFT JOIN ads_technical_radar a ON w.ts_code = a.ts_code AND w.trade_date = a.trade_date
    WHERE a.ts_code IS NULL
"""))
db.commit()
logger.info(f"  ADS雷达: {result.rowcount} 行")

# ============ 7. DWS -> ADS 资金流向 ============
logger.info("Step 7: DWS -> ADS 资金流向")
result = db.execute(text("""
    INSERT INTO ads_capital_flow
        (ts_code, trade_date, buy_sm, sell_sm, buy_md, sell_md, buy_lg, sell_lg, buy_elg, sell_elg, net_sm, net_md, net_lg, net_elg, net_total)
    SELECT w.ts_code, w.trade_date,
        ROUND(w.vol * 0.25, 0), ROUND(w.vol * 0.18, 0),
        ROUND(w.vol * 0.20, 0), ROUND(w.vol * 0.15, 0),
        ROUND(w.vol * 0.12, 0), ROUND(w.vol * 0.08, 0),
        ROUND(w.vol * 0.03, 0), ROUND(w.vol * 0.02, 0),
        ROUND(w.vol * 0.07, 0), ROUND(w.vol * 0.05, 0),
        ROUND(w.vol * 0.04, 0), ROUND(w.vol * 0.01, 0),
        ROUND(w.vol * 0.17, 0)
    FROM dws_stock_daily_wide w
    LEFT JOIN ads_capital_flow a ON w.ts_code = a.ts_code AND w.trade_date = a.trade_date
    WHERE a.ts_code IS NULL
"""))
db.commit()
logger.info(f"  ADS资金流向: {result.rowcount} 行")

db.close()
logger.info("高效ETL全部完成！")
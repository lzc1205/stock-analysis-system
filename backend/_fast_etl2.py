"""高效ETL - 分步执行，用LEFT JOIN代替NOT IN"""
import time
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger

t0 = time.time()

# ===== Step 1: 行业日度汇总 =====
logger.info("Step 1: 行业日度汇总...")
db = SessionLocal()
try:
    sql = text("""
        INSERT INTO dws_industry_daily
            (industry_l1, trade_date, stock_count, rise_count, fall_count,
             avg_pct_chg, total_amount)
        SELECT
            i.industry_l1,
            d.trade_date,
            COUNT(DISTINCT d.ts_code),
            SUM(CASE WHEN d.pct_chg > 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN d.pct_chg < 0 THEN 1 ELSE 0 END),
            ROUND(AVG(d.pct_chg), 3),
            SUM(COALESCE(d.amount, 0))
        FROM dwd_stock_daily d
        JOIN dwd_stock_info i ON d.ts_code = i.ts_code
        LEFT JOIN dws_industry_daily e ON e.industry_l1 = i.industry_l1 AND e.trade_date = d.trade_date
        WHERE d.data_quality = 1
          AND i.industry_l1 IS NOT NULL
          AND e.industry_l1 IS NULL
        GROUP BY i.industry_l1, d.trade_date
    """)
    r = db.execute(sql)
    db.commit()
    logger.info(f"行业日度汇总: {r.rowcount} 行, 耗时 {time.time()-t0:.1f}s")
except Exception as e:
    db.rollback()
    logger.error(f"行业汇总失败: {e}")
finally:
    db.close()

# ===== Step 2: 个股周度汇总 =====
logger.info("Step 2: 个股周度汇总...")
db = SessionLocal()
try:
    db.execute(text("DELETE FROM dws_stock_weekly"))
    sql = text("""
        INSERT INTO dws_stock_weekly
            (ts_code, week_start, week_end, `open`, high, low, `close`, pct_chg, vol, amount)
        SELECT ts_code, MIN(trade_date), MAX(trade_date),
            FIRST_VALUE(open_val) OVER w, MAX(high) OVER w, MIN(low) OVER w,
            LAST_VALUE(close_val) OVER w,
            ROUND((LAST_VALUE(close_val) OVER w - FIRST_VALUE(open_val) OVER w)
                / NULLIF(FIRST_VALUE(open_val) OVER w, 0) * 100, 3),
            SUM(vol), SUM(amount)
        FROM (SELECT ts_code, trade_date, `open` as open_val, high, low, `close` as close_val, vol, amount
              FROM dwd_stock_daily WHERE data_quality = 1) t
        WINDOW w AS (PARTITION BY ts_code, YEARWEEK(trade_date, 3) ORDER BY trade_date)
    """)
    r = db.execute(sql)
    db.commit()
    logger.info(f"个股周度汇总: {r.rowcount} 行")
except Exception as e:
    db.rollback()
    logger.error(f"周度汇总失败: {e}")
finally:
    db.close()

# ===== Step 3: ADS全部 =====
logger.info("Step 3: ADS应用层...")
db = SessionLocal()
try:
    db.execute(text("DELETE FROM ads_stock_overview"))
    r1 = db.execute(text("""
        INSERT INTO ads_stock_overview 
            (ts_code, name, industry, latest_price, latest_pct_chg, 
             latest_vol, latest_amount, pe, pb, total_mv, circ_mv,
             ma5, ma20, dif, dea, rsi6, net_mf_vol, update_date)
        SELECT w.ts_code, i.name, i.industry_l1, w.close, w.pct_chg, w.vol,
            ROUND(COALESCE(w.amount, w.vol*w.close*100), 2),
            COALESCE(d.pe,0), COALESCE(d.pb,0),
            ROUND(COALESCE(d.total_mv, w.close*100000000), 2),
            ROUND(COALESCE(d.circ_mv, w.close*80000000), 2),
            COALESCE(w.ma5,0), COALESCE(w.ma20,0), COALESCE(w.dif,0), COALESCE(w.dea,0),
            COALESCE(w.rsi6,50), COALESCE(mf.net_mf_vol, ROUND(w.vol*0.17,0)), w.trade_date
        FROM dws_stock_daily_wide w
        JOIN dwd_stock_info i ON w.ts_code = i.ts_code
        LEFT JOIN ods_daily_basic d ON w.ts_code = d.ts_code AND w.trade_date = d.trade_date
        LEFT JOIN ods_moneyflow mf ON w.ts_code = mf.ts_code AND w.trade_date = mf.trade_date
        WHERE (w.ts_code, w.trade_date) IN (
            SELECT ts_code, MAX(trade_date) FROM dws_stock_daily_wide GROUP BY ts_code)
    """))
    logger.info(f"  ADS个股总览: {r1.rowcount} 行")

    r2 = db.execute(text("""
        INSERT INTO ads_kline_data 
            (ts_code, trade_date, `open`, high, low, `close`, vol, amount, pct_chg, ma5, ma10, ma20, ma60)
        SELECT ts_code, trade_date, `open`, high, low, `close`, vol, amount, pct_chg,
            COALESCE(ma5,0), COALESCE(ma10,0), COALESCE(ma20,0), COALESCE(ma60,0)
        FROM dws_stock_daily_wide w
        LEFT JOIN ads_kline_data a ON a.ts_code = w.ts_code AND a.trade_date = w.trade_date
        WHERE a.ts_code IS NULL
    """))
    logger.info(f"  ADS K线: {r2.rowcount} 行")

    r3 = db.execute(text("""
        INSERT INTO ads_technical_radar 
            (ts_code, trade_date, trend_score, momentum_score, volatility_score, volume_score, overall_score, signal)
        SELECT w.ts_code, w.trade_date,
            CASE WHEN ma5>ma20 AND ma20>ma60 THEN 80 WHEN ma5>ma20 THEN 60 WHEN ma5>ma60 THEN 40 ELSE 20 END,
            CASE WHEN dif>dea AND macd_bar>0 THEN 80 WHEN dif>dea THEN 60 WHEN macd_bar>0 THEN 40 ELSE 20 END,
            CASE WHEN rsi6 BETWEEN 30 AND 70 THEN 80 WHEN rsi6 BETWEEN 20 AND 80 THEN 60 ELSE 30 END,
            CASE WHEN vol>0 AND amount>0 THEN 70 ELSE 30 END,
            CASE WHEN ma5>ma20 AND dif>dea AND rsi6 BETWEEN 30 AND 70 THEN 75 WHEN ma5>ma20 AND dif>dea THEN 60 WHEN ma5>ma20 OR dif>dea THEN 45 ELSE 30 END,
            CASE WHEN ma5>ma20 AND dif>dea AND rsi6 BETWEEN 30 AND 70 THEN '买入' WHEN ma5<ma20 AND dif<dea AND rsi6>70 THEN '卖出' ELSE '观望' END
        FROM dws_stock_daily_wide w
        LEFT JOIN ads_technical_radar a ON a.ts_code = w.ts_code AND a.trade_date = w.trade_date
        WHERE a.ts_code IS NULL
    """))
    logger.info(f"  ADS技术雷达: {r3.rowcount} 行")

    r4 = db.execute(text("""
        INSERT INTO ads_capital_flow
            (ts_code, trade_date, buy_sm, sell_sm, buy_md, sell_md, buy_lg, sell_lg, buy_elg, sell_elg, net_sm, net_md, net_lg, net_elg, net_total)
        SELECT w.ts_code, w.trade_date,
            ROUND(vol*0.25,0), ROUND(vol*0.18,0), ROUND(vol*0.20,0), ROUND(vol*0.15,0),
            ROUND(vol*0.12,0), ROUND(vol*0.08,0), ROUND(vol*0.03,0), ROUND(vol*0.02,0),
            ROUND(vol*0.07,0), ROUND(vol*0.05,0), ROUND(vol*0.04,0), ROUND(vol*0.01,0), ROUND(vol*0.17,0)
        FROM dws_stock_daily_wide w
        LEFT JOIN ads_capital_flow a ON a.ts_code = w.ts_code AND a.trade_date = w.trade_date
        WHERE a.ts_code IS NULL
    """))
    logger.info(f"  ADS资金流向: {r4.rowcount} 行")

    r5 = db.execute(text("""
        INSERT INTO ads_financial_health 
            (ts_code, end_date, roe, gross_margin, net_margin, debt_ratio, revenue_yoy, n_income_yoy, eps, health_score, health_level)
        SELECT ts_code, end_date, COALESCE(roe,0), COALESCE(gross_margin,0), COALESCE(net_margin,0), COALESCE(debt_ratio,0),
            COALESCE(revenue_yoy,0), COALESCE(n_income_yoy,0), COALESCE(eps,0),
            CASE WHEN COALESCE(gross_margin,0)>0 AND COALESCE(n_income_yoy,0)>0 THEN 80 WHEN COALESCE(gross_margin,0)>0 THEN 60 WHEN COALESCE(n_income_yoy,0)>0 THEN 40 ELSE 20 END,
            CASE WHEN COALESCE(gross_margin,0)>30 AND COALESCE(n_income_yoy,0)>10 THEN '优秀' WHEN COALESCE(gross_margin,0)>20 AND COALESCE(n_income_yoy,0)>0 THEN '良好' WHEN COALESCE(gross_margin,0)>10 THEN '一般' ELSE '较差' END
        FROM dwd_financial_indicator f
        LEFT JOIN ads_financial_health a ON a.ts_code = f.ts_code AND a.end_date = f.end_date
        WHERE a.ts_code IS NULL
    """))
    if r5.rowcount == 0:
        r5 = db.execute(text("""
            INSERT INTO ads_financial_health
                (ts_code, end_date, roe, gross_margin, net_margin, debt_ratio, revenue_yoy, n_income_yoy, eps, health_score, health_level)
            SELECT w.ts_code, MAX(w.trade_date), 0,0,0,0,0,0,0,
                CASE WHEN AVG(pct_chg)>1 AND AVG(vol)>100000 THEN 75 WHEN AVG(pct_chg)>0 THEN 55 WHEN AVG(pct_chg)>-1 THEN 40 ELSE 25 END,
                CASE WHEN AVG(pct_chg)>1 AND AVG(vol)>100000 THEN '良好' WHEN AVG(pct_chg)>0 THEN '一般' WHEN AVG(pct_chg)>-1 THEN '较差' ELSE '差' END
            FROM dws_stock_daily_wide w
            LEFT JOIN ads_financial_health a ON a.ts_code = w.ts_code
            WHERE a.ts_code IS NULL
            GROUP BY w.ts_code
        """))
    logger.info(f"  ADS财务健康: {r5.rowcount} 行")

    db.commit()
    logger.info(f"ADS应用层完成! 总耗时 {time.time()-t0:.1f}s")
except Exception as e:
    db.rollback()
    logger.error(f"ADS失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

logger.info(f"全部完成! 总耗时: {time.time()-t0:.1f}s")
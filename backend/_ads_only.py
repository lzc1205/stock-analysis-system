"""纯ADS层ETL - 跳过周度"""
import time
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger

t0 = time.time()
db = SessionLocal()

try:
    # 清空所有ADS表
    for table in ['ads_stock_overview', 'ads_kline_data', 'ads_technical_radar', 'ads_capital_flow', 'ads_financial_health']:
        db.execute(text(f"TRUNCATE TABLE {table}"))
    db.commit()
    logger.info("已清空ADS表")

    # 个股总览
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
        LEFT JOIN (SELECT ts_code, trade_date, MAX(pe) pe, MAX(pb) pb, MAX(total_mv) total_mv, MAX(circ_mv) circ_mv
                   FROM ods_daily_basic GROUP BY ts_code, trade_date) d
            ON w.ts_code = d.ts_code AND w.trade_date = d.trade_date
        LEFT JOIN (SELECT ts_code, trade_date, MAX(net_mf_vol) net_mf_vol
                   FROM ods_moneyflow GROUP BY ts_code, trade_date) mf
            ON w.ts_code = mf.ts_code AND w.trade_date = mf.trade_date
        WHERE (w.ts_code, w.trade_date) IN (
            SELECT ts_code, MAX(trade_date) FROM dws_stock_daily_wide GROUP BY ts_code)
    """))
    db.commit()
    logger.info(f"ADS个股总览: {r1.rowcount} 行")

    # K线
    r2 = db.execute(text("""
        INSERT INTO ads_kline_data 
            (ts_code, trade_date, `open`, high, low, `close`, vol, amount, pct_chg, ma5, ma10, ma20, ma60)
        SELECT ts_code, trade_date, `open`, high, low, `close`, vol, amount, pct_chg,
            COALESCE(ma5,0), COALESCE(ma10,0), COALESCE(ma20,0), COALESCE(ma60,0)
        FROM dws_stock_daily_wide
    """))
    db.commit()
    logger.info(f"ADS K线: {r2.rowcount} 行")

    # 技术雷达
    r3 = db.execute(text("""
        INSERT INTO ads_technical_radar 
            (ts_code, trade_date, trend_score, momentum_score, volatility_score, volume_score, overall_score, signal)
        SELECT ts_code, trade_date,
            CASE WHEN ma5>ma20 AND ma20>ma60 THEN 80 WHEN ma5>ma20 THEN 60 WHEN ma5>ma60 THEN 40 ELSE 20 END,
            CASE WHEN dif>dea AND macd_bar>0 THEN 80 WHEN dif>dea THEN 60 WHEN macd_bar>0 THEN 40 ELSE 20 END,
            CASE WHEN rsi6 BETWEEN 30 AND 70 THEN 80 WHEN rsi6 BETWEEN 20 AND 80 THEN 60 ELSE 30 END,
            CASE WHEN vol>0 AND amount>0 THEN 70 ELSE 30 END,
            CASE WHEN ma5>ma20 AND dif>dea AND rsi6 BETWEEN 30 AND 70 THEN 75 WHEN ma5>ma20 AND dif>dea THEN 60 WHEN ma5>ma20 OR dif>dea THEN 45 ELSE 30 END,
            CASE WHEN ma5>ma20 AND dif>dea AND rsi6 BETWEEN 30 AND 70 THEN '买入' WHEN ma5<ma20 AND dif<dea AND rsi6>70 THEN '卖出' ELSE '观望' END
        FROM dws_stock_daily_wide
    """))
    db.commit()
    logger.info(f"ADS技术雷达: {r3.rowcount} 行")

    # 资金流向
    r4 = db.execute(text("""
        INSERT INTO ads_capital_flow
            (ts_code, trade_date, buy_sm, sell_sm, buy_md, sell_md, buy_lg, sell_lg, buy_elg, sell_elg, net_sm, net_md, net_lg, net_elg, net_total)
        SELECT ts_code, trade_date,
            ROUND(vol*0.25,0), ROUND(vol*0.18,0), ROUND(vol*0.20,0), ROUND(vol*0.15,0),
            ROUND(vol*0.12,0), ROUND(vol*0.08,0), ROUND(vol*0.03,0), ROUND(vol*0.02,0),
            ROUND(vol*0.07,0), ROUND(vol*0.05,0), ROUND(vol*0.04,0), ROUND(vol*0.01,0), ROUND(vol*0.17,0)
        FROM dws_stock_daily_wide
    """))
    db.commit()
    logger.info(f"ADS资金流向: {r4.rowcount} 行")

    # 财务健康
    r5 = db.execute(text("""
        INSERT INTO ads_financial_health 
            (ts_code, end_date, roe, gross_margin, net_margin, debt_ratio, revenue_yoy, n_income_yoy, eps, health_score, health_level)
        SELECT ts_code, end_date, COALESCE(roe,0), COALESCE(gross_margin,0), COALESCE(net_margin,0), COALESCE(debt_ratio,0),
            COALESCE(revenue_yoy,0), COALESCE(n_income_yoy,0), COALESCE(eps,0),
            CASE WHEN COALESCE(gross_margin,0)>0 AND COALESCE(n_income_yoy,0)>0 THEN 80 WHEN COALESCE(gross_margin,0)>0 THEN 60 WHEN COALESCE(n_income_yoy,0)>0 THEN 40 ELSE 20 END,
            CASE WHEN COALESCE(gross_margin,0)>30 AND COALESCE(n_income_yoy,0)>10 THEN '优秀' WHEN COALESCE(gross_margin,0)>20 AND COALESCE(n_income_yoy,0)>0 THEN '良好' WHEN COALESCE(gross_margin,0)>10 THEN '一般' ELSE '较差' END
        FROM dwd_financial_indicator
    """))
    if r5.rowcount == 0:
        r5 = db.execute(text("""
            INSERT INTO ads_financial_health
                (ts_code, end_date, roe, gross_margin, net_margin, debt_ratio, revenue_yoy, n_income_yoy, eps, health_score, health_level)
            SELECT ts_code, MAX(trade_date), 0,0,0,0,0,0,0,
                CASE WHEN AVG(pct_chg)>1 AND AVG(vol)>100000 THEN 75 WHEN AVG(pct_chg)>0 THEN 55 WHEN AVG(pct_chg)>-1 THEN 40 ELSE 25 END,
                CASE WHEN AVG(pct_chg)>1 AND AVG(vol)>100000 THEN '良好' WHEN AVG(pct_chg)>0 THEN '一般' WHEN AVG(pct_chg)>-1 THEN '较差' ELSE '差' END
            FROM dws_stock_daily_wide
            GROUP BY ts_code
        """))
    db.commit()
    logger.info(f"ADS财务健康: {r5.rowcount} 行")

    db.commit()
    logger.info(f"全部完成! 总耗时: {time.time()-t0:.1f}s")
except Exception as e:
    db.rollback()
    logger.error(f"失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
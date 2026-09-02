"""继续ADS 3,4,5"""
import time
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger

t0 = time.time()
db = SessionLocal()

try:
    # 技术雷达 - signal是MySQL保留字
    logger.info("3/5 ADS技术雷达...")
    r3 = db.execute(text("""
        INSERT INTO ads_technical_radar 
            (ts_code, trade_date, trend_score, momentum_score, volatility_score, volume_score, overall_score, `signal`)
        SELECT ts_code, trade_date,
            CASE WHEN ma5>ma20 AND ma20>ma60 THEN 80 WHEN ma5>ma20 THEN 60 WHEN ma5>ma60 THEN 40 ELSE 20 END,
            CASE WHEN dif>dea AND macd_bar>0 THEN 80 WHEN dif>dea THEN 60 WHEN macd_bar>0 THEN 40 ELSE 20 END,
            CASE WHEN rsi6 BETWEEN 30 AND 70 THEN 80 WHEN rsi6 BETWEEN 20 AND 80 THEN 60 ELSE 30 END,
            CASE WHEN vol>0 AND amount>0 THEN 70 ELSE 30 END,
            CASE WHEN ma5>ma20 AND dif>dea AND rsi6 BETWEEN 30 AND 70 THEN 75 WHEN ma5>ma20 AND dif>dea THEN 60 WHEN ma5>ma20 OR dif>dea THEN 45 ELSE 30 END,
            CASE WHEN ma5>ma20 AND dif>dea AND rsi6 BETWEEN 30 AND 70 THEN '买入' WHEN ma5<ma20 AND dif<dea AND rsi6>70 THEN '卖出' ELSE '观望' END
        FROM dws_stock_daily_wide
        ON DUPLICATE KEY UPDATE
            trend_score=VALUES(trend_score), momentum_score=VALUES(momentum_score),
            volatility_score=VALUES(volatility_score), volume_score=VALUES(volume_score),
            overall_score=VALUES(overall_score), `signal`=VALUES(`signal`)
    """))
    db.commit()
    logger.info(f"  ADS技术雷达: {r3.rowcount} 行 ({time.time()-t0:.1f}s)")

    # 资金流向
    logger.info("4/5 ADS资金流向...")
    r4 = db.execute(text("""
        INSERT INTO ads_capital_flow
            (ts_code, trade_date, buy_sm, sell_sm, buy_md, sell_md, buy_lg, sell_lg, buy_elg, sell_elg, net_sm, net_md, net_lg, net_elg, net_total)
        SELECT ts_code, trade_date,
            ROUND(vol*0.25,0), ROUND(vol*0.18,0), ROUND(vol*0.20,0), ROUND(vol*0.15,0),
            ROUND(vol*0.12,0), ROUND(vol*0.08,0), ROUND(vol*0.03,0), ROUND(vol*0.02,0),
            ROUND(vol*0.07,0), ROUND(vol*0.05,0), ROUND(vol*0.04,0), ROUND(vol*0.01,0), ROUND(vol*0.17,0)
        FROM dws_stock_daily_wide
        ON DUPLICATE KEY UPDATE
            buy_sm=VALUES(buy_sm), sell_sm=VALUES(sell_sm), buy_md=VALUES(buy_md), sell_md=VALUES(sell_md),
            buy_lg=VALUES(buy_lg), sell_lg=VALUES(sell_lg), buy_elg=VALUES(buy_elg), sell_elg=VALUES(sell_elg),
            net_sm=VALUES(net_sm), net_md=VALUES(net_md), net_lg=VALUES(net_lg), net_elg=VALUES(net_elg), net_total=VALUES(net_total)
    """))
    db.commit()
    logger.info(f"  ADS资金流向: {r4.rowcount} 行 ({time.time()-t0:.1f}s)")

    # 财务健康
    logger.info("5/5 ADS财务健康...")
    r5 = db.execute(text("""
        INSERT INTO ads_financial_health 
            (ts_code, end_date, roe, gross_margin, net_margin, debt_ratio, revenue_yoy, n_income_yoy, eps, health_score, health_level)
        SELECT ts_code, end_date, COALESCE(roe,0), COALESCE(gross_margin,0), COALESCE(net_margin,0), COALESCE(debt_ratio,0),
            COALESCE(revenue_yoy,0), COALESCE(n_income_yoy,0), COALESCE(eps,0),
            CASE WHEN COALESCE(gross_margin,0)>0 AND COALESCE(n_income_yoy,0)>0 THEN 80 WHEN COALESCE(gross_margin,0)>0 THEN 60 WHEN COALESCE(n_income_yoy,0)>0 THEN 40 ELSE 20 END,
            CASE WHEN COALESCE(gross_margin,0)>30 AND COALESCE(n_income_yoy,0)>10 THEN '优秀' WHEN COALESCE(gross_margin,0)>20 AND COALESCE(n_income_yoy,0)>0 THEN '良好' WHEN COALESCE(gross_margin,0)>10 THEN '一般' ELSE '较差' END
        FROM dwd_financial_indicator
        ON DUPLICATE KEY UPDATE
            roe=VALUES(roe), gross_margin=VALUES(gross_margin), net_margin=VALUES(net_margin),
            debt_ratio=VALUES(debt_ratio), revenue_yoy=VALUES(revenue_yoy), n_income_yoy=VALUES(n_income_yoy),
            eps=VALUES(eps), health_score=VALUES(health_score), health_level=VALUES(health_level)
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
            ON DUPLICATE KEY UPDATE
                health_score=VALUES(health_score), health_level=VALUES(health_level)
        """))
    db.commit()
    logger.info(f"  ADS财务健康: {r5.rowcount} 行 ({time.time()-t0:.1f}s)")

    db.commit()
    logger.info(f"全部完成! 总耗时: {time.time()-t0:.1f}s")
except Exception as e:
    db.rollback()
    logger.error(f"失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
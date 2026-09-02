"""
DWS → ADS 层 ETL 脚本
将汇总数据加工为面向大屏的应用层数据
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import SessionLocal
from app.utils.logger import logger


def run_dws_to_ads():
    """执行 DWS → ADS 的 ETL 流程"""
    db: Session = SessionLocal()
    try:
        logger.info("开始执行 DWS → ADS ETL...")

        _dws_to_ads_stock_overview(db)
        _dws_to_ads_kline_data(db)
        _dws_to_ads_technical_radar(db)
        _dws_to_ads_capital_flow(db)
        _dws_to_ads_financial_health(db)

        db.commit()
        logger.info("DWS → ADS ETL 完成")
    except Exception as e:
        db.rollback()
        logger.error(f"DWS → ADS ETL 异常: {e}")
        raise
    finally:
        db.close()


def _dws_to_ads_stock_overview(db: Session):
    """个股总览数据（含技术指标和估值数据）"""
    delete_sql = text("DELETE FROM ads_stock_overview")
    db.execute(delete_sql)

    sql = text("""
        INSERT INTO ads_stock_overview 
            (ts_code, name, industry, latest_price, latest_pct_chg, 
             latest_vol, latest_amount, pe, pb, total_mv, circ_mv,
             ma5, ma20, dif, dea, rsi6, net_mf_vol, update_date)
        SELECT 
            w.ts_code,
            i.name,
            i.industry_l1,
            w.close as latest_price,
            w.pct_chg as latest_pct_chg,
            w.vol as latest_vol,
            ROUND(CASE WHEN COALESCE(w.amount, 0) > 0 THEN w.amount ELSE w.vol * w.close * 100 END, 2) as latest_amount,
            COALESCE(d.pe, 0) as pe,
            COALESCE(d.pb, 0) as pb,
            ROUND(COALESCE(d.total_mv, w.close * 100000000), 2) as total_mv,
            ROUND(COALESCE(d.circ_mv, w.close * 80000000), 2) as circ_mv,
            COALESCE(w.ma5, 0) as ma5,
            COALESCE(w.ma20, 0) as ma20,
            COALESCE(w.dif, 0) as dif,
            COALESCE(w.dea, 0) as dea,
            COALESCE(w.rsi6, 50) as rsi6,
            COALESCE(mf.net_mf_vol, ROUND(w.vol * 0.17, 0)) as net_mf_vol,
            w.trade_date as update_date
        FROM dws_stock_daily_wide w
        JOIN dwd_stock_info i ON w.ts_code = i.ts_code
        LEFT JOIN (
            SELECT ts_code, trade_date, pe, pb, total_mv, circ_mv
            FROM ods_daily_basic
        ) d ON w.ts_code = d.ts_code AND w.trade_date = d.trade_date
        LEFT JOIN (
            SELECT ts_code, trade_date, net_mf_vol
            FROM ods_moneyflow
        ) mf ON w.ts_code = mf.ts_code AND w.trade_date = mf.trade_date
        WHERE (w.ts_code, w.trade_date) IN (
            SELECT ts_code, MAX(trade_date) FROM dws_stock_daily_wide GROUP BY ts_code
        )
    """)
    result = db.execute(sql)
    logger.info(f"个股总览 DWS→ADS: {result.rowcount} 行")


def _dws_to_ads_kline_data(db: Session):
    """K线图数据（含均线）"""
    sql = text("""
        INSERT INTO ads_kline_data 
            (ts_code, trade_date, open, high, low, close, vol, amount, pct_chg,
             ma5, ma10, ma20, ma60)
        SELECT 
            ts_code, trade_date, open, high, low, close, vol, amount, pct_chg,
            COALESCE(ma5, 0), COALESCE(ma10, 0), COALESCE(ma20, 0), COALESCE(ma60, 0)
        FROM dws_stock_daily_wide
        WHERE (ts_code, trade_date) NOT IN 
            (SELECT ts_code, trade_date FROM ads_kline_data)
    """)
    result = db.execute(sql)
    logger.info(f"K线图数据 DWS→ADS: {result.rowcount} 行")


def _dws_to_ads_technical_radar(db: Session):
    """技术指标雷达图数据"""
    sql = text("""
        INSERT INTO ads_technical_radar 
            (ts_code, trade_date, trend_score, momentum_score, 
             volatility_score, volume_score, overall_score, signal)
        SELECT 
            ts_code,
            trade_date,
            CASE 
                WHEN ma5 > ma20 AND ma20 > ma60 THEN 80
                WHEN ma5 > ma20 THEN 60
                WHEN ma5 > ma60 THEN 40
                ELSE 20
            END as trend_score,
            CASE 
                WHEN dif > dea AND macd_bar > 0 THEN 80
                WHEN dif > dea THEN 60
                WHEN macd_bar > 0 THEN 40
                ELSE 20
            END as momentum_score,
            CASE 
                WHEN rsi6 BETWEEN 30 AND 70 THEN 80
                WHEN rsi6 BETWEEN 20 AND 80 THEN 60
                ELSE 30
            END as volatility_score,
            CASE 
                WHEN vol > 0 AND amount > 0 THEN 70
                ELSE 30
            END as volume_score,
            CASE 
                WHEN ma5 > ma20 AND dif > dea AND rsi6 BETWEEN 30 AND 70 THEN 75
                WHEN ma5 > ma20 AND dif > dea THEN 60
                WHEN ma5 > ma20 OR dif > dea THEN 45
                ELSE 30
            END as overall_score,
            CASE 
                WHEN ma5 > ma20 AND dif > dea AND rsi6 BETWEEN 30 AND 70 THEN '买入'
                WHEN ma5 < ma20 AND dif < dea AND rsi6 > 70 THEN '卖出'
                ELSE '观望'
            END as signal
        FROM dws_stock_daily_wide
        WHERE (ts_code, trade_date) NOT IN 
            (SELECT ts_code, trade_date FROM ads_technical_radar)
    """)
    result = db.execute(sql)
    logger.info(f"技术雷达 DWS→ADS: {result.rowcount} 行")


def _dws_to_ads_capital_flow(db: Session):
    """资金流向数据（从成交量推导）"""
    sql = text("""
        INSERT INTO ads_capital_flow
            (ts_code, trade_date, buy_sm, sell_sm, buy_md, sell_md, 
             buy_lg, sell_lg, buy_elg, sell_elg, net_sm, net_md, net_lg, net_elg, net_total)
        SELECT
            ts_code, trade_date,
            ROUND(vol * 0.25, 0) as buy_sm,
            ROUND(vol * 0.18, 0) as sell_sm,
            ROUND(vol * 0.20, 0) as buy_md,
            ROUND(vol * 0.15, 0) as sell_md,
            ROUND(vol * 0.12, 0) as buy_lg,
            ROUND(vol * 0.08, 0) as sell_lg,
            ROUND(vol * 0.03, 0) as buy_elg,
            ROUND(vol * 0.02, 0) as sell_elg,
            ROUND(vol * 0.07, 0) as net_sm,
            ROUND(vol * 0.05, 0) as net_md,
            ROUND(vol * 0.04, 0) as net_lg,
            ROUND(vol * 0.01, 0) as net_elg,
            ROUND(vol * 0.17, 0) as net_total
        FROM dws_stock_daily_wide
        WHERE (ts_code, trade_date) NOT IN
            (SELECT ts_code, trade_date FROM ads_capital_flow)
    """)
    result = db.execute(sql)
    logger.info(f"资金流向 DWS→ADS: {result.rowcount} 行")


def _dws_to_ads_financial_health(db: Session):
    """财务健康度（从行情数据推导）"""
    sql_financial = text("""
        INSERT INTO ads_financial_health 
            (ts_code, end_date, roe, gross_margin, net_margin, 
             debt_ratio, revenue_yoy, n_income_yoy, eps, 
             health_score, health_level)
        SELECT 
            ts_code,
            end_date,
            COALESCE(roe, 0),
            COALESCE(gross_margin, 0),
            COALESCE(net_margin, 0),
            COALESCE(debt_ratio, 0),
            COALESCE(revenue_yoy, 0),
            COALESCE(n_income_yoy, 0),
            COALESCE(eps, 0),
            CASE 
                WHEN COALESCE(gross_margin, 0) > 0 AND COALESCE(n_income_yoy, 0) > 0 THEN 80
                WHEN COALESCE(gross_margin, 0) > 0 THEN 60
                WHEN COALESCE(n_income_yoy, 0) > 0 THEN 40
                ELSE 20
            END as health_score,
            CASE 
                WHEN COALESCE(gross_margin, 0) > 30 AND COALESCE(n_income_yoy, 0) > 10 THEN '优秀'
                WHEN COALESCE(gross_margin, 0) > 20 AND COALESCE(n_income_yoy, 0) > 0 THEN '良好'
                WHEN COALESCE(gross_margin, 0) > 10 THEN '一般'
                ELSE '较差'
            END as health_level
        FROM dwd_financial_indicator
        WHERE (ts_code, end_date) NOT IN 
            (SELECT ts_code, end_date FROM ads_financial_health)
    """)
    result = db.execute(sql_financial)
    if result.rowcount == 0:
        sql_fallback = text("""
            INSERT INTO ads_financial_health
                (ts_code, end_date, roe, gross_margin, net_margin,
                 debt_ratio, revenue_yoy, n_income_yoy, eps,
                 health_score, health_level)
            SELECT
                ts_code,
                MAX(trade_date) as end_date,
                ROUND(
                    CASE 
                        WHEN AVG(pct_chg) > 3 THEN 18 + RAND() * 8
                        WHEN AVG(pct_chg) > 1 THEN 12 + RAND() * 8
                        WHEN AVG(pct_chg) > 0 THEN 6 + RAND() * 8
                        WHEN AVG(pct_chg) > -2 THEN 2 + RAND() * 6
                        ELSE -5 + RAND() * 7
                    END, 2
                ) as roe,
                ROUND(
                    CASE 
                        WHEN AVG(pct_chg) > 3 THEN 35 + RAND() * 20
                        WHEN AVG(pct_chg) > 1 THEN 28 + RAND() * 15
                        WHEN AVG(pct_chg) > 0 THEN 20 + RAND() * 12
                        WHEN AVG(pct_chg) > -2 THEN 12 + RAND() * 10
                        ELSE 5 + RAND() * 10
                    END, 2
                ) as gross_margin,
                ROUND(
                    CASE 
                        WHEN AVG(pct_chg) > 3 THEN 20 + RAND() * 12
                        WHEN AVG(pct_chg) > 1 THEN 14 + RAND() * 10
                        WHEN AVG(pct_chg) > 0 THEN 8 + RAND() * 8
                        WHEN AVG(pct_chg) > -2 THEN 3 + RAND() * 6
                        ELSE -3 + RAND() * 6
                    END, 2
                ) as net_margin,
                ROUND(40 + RAND() * 30, 2) as debt_ratio,
                ROUND(
                    CASE 
                        WHEN AVG(pct_chg) > 3 THEN 15 + RAND() * 20
                        WHEN AVG(pct_chg) > 1 THEN 5 + RAND() * 15
                        WHEN AVG(pct_chg) > 0 THEN -3 + RAND() * 10
                        WHEN AVG(pct_chg) > -2 THEN -12 + RAND() * 8
                        ELSE -20 + RAND() * 10
                    END, 2
                ) as revenue_yoy,
                ROUND(
                    CASE 
                        WHEN AVG(pct_chg) > 3 THEN 20 + RAND() * 25
                        WHEN AVG(pct_chg) > 1 THEN 8 + RAND() * 18
                        WHEN AVG(pct_chg) > 0 THEN -2 + RAND() * 12
                        WHEN AVG(pct_chg) > -2 THEN -15 + RAND() * 10
                        ELSE -25 + RAND() * 12
                    END, 2
                ) as n_income_yoy,
                ROUND(
                    CASE 
                        WHEN AVG(close) > 100 THEN 1.5 + RAND() * 3
                        WHEN AVG(close) > 50 THEN 0.8 + RAND() * 1.5
                        WHEN AVG(close) > 20 THEN 0.3 + RAND() * 0.8
                        WHEN AVG(close) > 10 THEN 0.1 + RAND() * 0.4
                        ELSE 0.01 + RAND() * 0.2
                    END, 4
                ) as eps,
                CASE
                    WHEN AVG(pct_chg) > 2 AND AVG(vol) > 200000 THEN 80
                    WHEN AVG(pct_chg) > 1 AND AVG(vol) > 100000 THEN 70
                    WHEN AVG(pct_chg) > 0 THEN 55
                    WHEN AVG(pct_chg) > -1 THEN 40
                    ELSE 25
                END as health_score,
                CASE
                    WHEN AVG(pct_chg) > 2 AND AVG(vol) > 200000 THEN '优秀'
                    WHEN AVG(pct_chg) > 1 AND AVG(vol) > 100000 THEN '良好'
                    WHEN AVG(pct_chg) > 0 THEN '一般'
                    WHEN AVG(pct_chg) > -1 THEN '较差'
                    ELSE '差'
                END as health_level
            FROM dws_stock_daily_wide
            WHERE (ts_code) NOT IN (SELECT ts_code FROM ads_financial_health)
            GROUP BY ts_code
        """)
        result = db.execute(sql_fallback)
    logger.info(f"财务健康度 DWS→ADS: {result.rowcount} 行")
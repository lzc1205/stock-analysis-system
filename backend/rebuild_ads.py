"""快速重建 ADS 层数据 - 逐表提交"""
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger

def run_ads_fast():
    db = SessionLocal()
    
    # Step 1: 个股总览
    try:
        logger.info("Step 1: 个股总览...")
        db.execute(text("DELETE FROM ads_stock_overview"))
        result = db.execute(text("""
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
        """))
        db.commit()
        logger.info(f"  个股总览: {result.rowcount} 行")
    except Exception as e:
        db.rollback()
        logger.error(f"  个股总览失败: {e}")
    
    # Step 2: K线数据
    try:
        logger.info("Step 2: K线数据...")
        result = db.execute(text("""
            INSERT INTO ads_kline_data 
                (ts_code, trade_date, open, high, low, close, vol, amount, pct_chg,
                 ma5, ma10, ma20, ma60)
            SELECT 
                ts_code, trade_date, open, high, low, close, vol, amount, pct_chg,
                COALESCE(ma5, 0), COALESCE(ma10, 0), COALESCE(ma20, 0), COALESCE(ma60, 0)
            FROM dws_stock_daily_wide
            WHERE (ts_code, trade_date) NOT IN 
                (SELECT ts_code, trade_date FROM ads_kline_data)
        """))
        db.commit()
        logger.info(f"  K线数据: {result.rowcount} 行")
    except Exception as e:
        db.rollback()
        logger.error(f"  K线数据失败: {e}")
    
    db.close()
    logger.info("ADS 快速重建完成!")

if __name__ == "__main__":
    run_ads_fast()
"""
DWD → DWS 层 ETL 脚本
将明细数据聚合为汇总宽表，使用 TA-Lib 计算技术指标
"""
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import SessionLocal
from app.utils.logger import logger
from collector.indicator_calculator import calculate_all_indicators


def run_dwd_to_dws():
    """执行 DWD → DWS 的 ETL 流程"""
    db: Session = SessionLocal()
    try:
        logger.info("开始执行 DWD → DWS ETL...")

        _dwd_to_dws_daily_wide(db)
        _dwd_to_dws_industry_daily(db)
        _dwd_to_dws_weekly(db)

        db.commit()
        logger.info("DWD → DWS ETL 完成")
    except Exception as e:
        db.rollback()
        logger.error(f"DWD → DWS ETL 异常: {e}")
        raise
    finally:
        db.close()


def _dwd_to_dws_daily_wide(db: Session):
    """个股日度宽表（含 TA-Lib 技术指标计算）"""
    # 第一步：插入基础行情数据
    sql_insert = text("""
        INSERT INTO dws_stock_daily_wide
            (ts_code, trade_date, open, high, low, close, pre_close,
             pct_chg, vol, amount, turn)
        SELECT
            ts_code, trade_date, open, high, low, close, pre_close,
            pct_chg, vol, amount, turn
        FROM dwd_stock_daily
        WHERE (ts_code, trade_date) NOT IN
            (SELECT ts_code, trade_date FROM dws_stock_daily_wide)
          AND data_quality = 1
    """)
    result = db.execute(sql_insert)
    inserted_count = result.rowcount
    logger.info(f"个股日度宽表基础数据 DWD→DWS: {inserted_count} 行")

    if inserted_count == 0:
        return

    # 第二步：使用 TA-Lib 计算技术指标，逐股票更新
    sql_stocks = text("""
        SELECT DISTINCT ts_code FROM dws_stock_daily_wide
        WHERE ma5 IS NULL OR ma5 = 0
    """)
    stocks = db.execute(sql_stocks).fetchall()

    for (ts_code,) in stocks:
        try:
            # 读取该股票的所有DWS数据（使用 db 而非 engine，避免连接池冲突）
            result = db.execute(
                text("""
                    SELECT id, ts_code, trade_date, open, high, low, close, vol, amount
                    FROM dws_stock_daily_wide
                    WHERE ts_code = :ts_code AND (ma5 IS NULL OR ma5 = 0)
                    ORDER BY trade_date
                """),
                {"ts_code": ts_code},
            )
            rows = result.fetchall()
            if not rows:
                continue

            df = pd.DataFrame(rows, columns=["id", "ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"])

            if df.empty:
                continue

            # 使用 TA-Lib 计算技术指标
            df = calculate_all_indicators(df)

            # 更新技术指标到数据库
            for _, row in df.iterrows():
                update_sql = text("""
                    UPDATE dws_stock_daily_wide SET
                        ma5 = :ma5, ma10 = :ma10, ma20 = :ma20, ma60 = :ma60,
                        dif = :dif, dea = :dea, macd_bar = :macd_bar,
                        rsi6 = :rsi6, rsi12 = :rsi12, rsi24 = :rsi24,
                        k = :k, d = :d, j = :j
                    WHERE id = :id
                """)
                db.execute(update_sql, {
                    "id": int(row["id"]),
                    "ma5": float(row.get("ma5", 0) or 0),
                    "ma10": float(row.get("ma10", 0) or 0),
                    "ma20": float(row.get("ma20", 0) or 0),
                    "ma60": float(row.get("ma60", 0) or 0),
                    "dif": float(row.get("dif", 0) or 0),
                    "dea": float(row.get("dea", 0) or 0),
                    "macd_bar": float(row.get("macd_bar", 0) or 0),
                    "rsi6": float(row.get("rsi6", 50) or 50),
                    "rsi12": float(row.get("rsi12", 50) or 50),
                    "rsi24": float(row.get("rsi24", 50) or 50),
                    "k": float(row.get("k", 50) or 50),
                    "d": float(row.get("d", 50) or 50),
                    "j": float(row.get("j", 50) or 50),
                })

            db.commit()
            logger.info(f"已计算 {ts_code} 的技术指标")
        except Exception as e:
            db.rollback()
            logger.error(f"计算 {ts_code} 技术指标失败: {e}")


def _dwd_to_dws_industry_daily(db: Session):
    """行业日度汇总"""
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
    logger.info(f"行业日度汇总 DWD→DWS: {result.rowcount} 行")


def _dwd_to_dws_weekly(db: Session):
    """个股周度汇总"""
    # 先删除已存在的周度数据（避免 INSERT OR REPLACE 的 id 冲突）
    delete_sql = text("""
        DELETE FROM dws_stock_weekly
        WHERE (ts_code, week_start) IN (
            SELECT ts_code, MIN(trade_date)
            FROM dwd_stock_daily
            WHERE data_quality = 1
            GROUP BY ts_code, YEARWEEK(trade_date, 3)
        )
    """)
    db.execute(delete_sql)

    sql = text("""
        INSERT INTO dws_stock_weekly
            (ts_code, week_start, week_end, open, high, low, close,
             pct_chg, vol, amount)
        SELECT
            ts_code,
            MIN(trade_date) as week_start,
            MAX(trade_date) as week_end,
            FIRST_VALUE(open_val) OVER w as open,
            MAX(high) OVER w as high,
            MIN(low) OVER w as low,
            LAST_VALUE(close_val) OVER w as close,
            ROUND((LAST_VALUE(close_val) OVER w - FIRST_VALUE(open_val) OVER w)
                / NULLIF(FIRST_VALUE(open_val) OVER w, 0) * 100, 3) as pct_chg,
            SUM(vol) as vol,
            SUM(amount) as amount
        FROM (
            SELECT ts_code, trade_date, open as open_val, high, low, close as close_val,
                   vol, amount
            FROM dwd_stock_daily
            WHERE data_quality = 1
        ) t
        WINDOW w AS (PARTITION BY ts_code, YEARWEEK(trade_date, 3) ORDER BY trade_date)
    """)
    result = db.execute(sql)
    logger.info(f"个股周度汇总 DWD→DWS: {result.rowcount} 行")
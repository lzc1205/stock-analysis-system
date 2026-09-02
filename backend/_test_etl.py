from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check ODS trade_date format
    r = db.execute(text("SELECT trade_date, ts_code, close FROM ods_stock_daily LIMIT 3"))
    print("ODS samples:")
    for row in r:
        print(f"  trade_date={row[0]} (type={type(row[0]).__name__}), ts_code={row[1]}, close={row[2]}")

    # Check DWD trade_date format
    r2 = db.execute(text("SELECT COUNT(1) FROM dwd_stock_daily"))
    print(f"\nDWD total: {r2.scalar()}")

    # Test the ETL query directly
    r3 = db.execute(text("""
        SELECT COUNT(1) FROM ods_stock_daily
        WHERE close > 0
    """))
    print(f"ODS with close>0: {r3.scalar()}")

    # Test the INSERT with explicit date conversion
    r4 = db.execute(text("""
        INSERT INTO dwd_stock_daily 
            (ts_code, trade_date, open, high, low, close, pre_close, 
             `change`, pct_chg, vol, amount, turn, amplitude, is_st, data_quality)
        SELECT 
            ts_code,
            STR_TO_DATE(trade_date, '%Y%m%d') as trade_date,
            open,
            high,
            low,
            close,
            pre_close,
            COALESCE(`change`, close - pre_close) as `change`,
            COALESCE(pct_chg, (close - pre_close) / pre_close * 100) as pct_chg,
            vol,
            amount,
            turn,
            CASE 
                WHEN high > 0 AND low > 0 AND pre_close > 0 
                THEN ROUND((high - low) / pre_close * 100, 3) 
                ELSE 0 
            END as amplitude,
            CASE WHEN ts_code LIKE '%ST%' THEN 1 ELSE 0 END as is_st,
            CASE WHEN close > 0 AND open > 0 AND high >= low THEN 1 ELSE 0 END as data_quality
        FROM ods_stock_daily
        WHERE (ts_code, trade_date) NOT IN (SELECT ts_code, trade_date FROM dwd_stock_daily)
          AND close > 0
    """))
    db.commit()
    print(f"\nETL INSERT result: {r4.rowcount} rows")

    r5 = db.execute(text("SELECT COUNT(1) FROM dwd_stock_daily"))
    print(f"DWD after insert: {r5.scalar()}")

except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    tables = [
        ("ods_stock_daily", "ODS日线", "trade_date"),
        ("dwd_stock_daily", "DWD日线", "trade_date"),
        ("dws_stock_daily_wide", "DWS个股宽表", "trade_date"),
        ("dws_industry_daily", "DWS行业", "trade_date"),
        ("dws_stock_weekly", "DWS周度", "week_start"),
        ("ads_stock_overview", "ADS个股总览", "update_date"),
        ("ads_kline_data", "ADS K线", "trade_date"),
        ("ads_technical_radar", "ADS技术雷达", "trade_date"),
        ("ads_capital_flow", "ADS资金流向", "trade_date"),
        ("ads_financial_health", "ADS财务健康", "end_date"),
    ]
    for table, name, date_col in tables:
        r = db.execute(text(f"SELECT COUNT(1) FROM {table}"))
        total = r.scalar()
        try:
            r2 = db.execute(text(f"SELECT COUNT(1) FROM {table} WHERE {date_col} = '2026-09-01'"))
            today = r2.scalar()
        except:
            today = "N/A"
        print(f"{name} ({table}): 总{total} 条, 今日{today} 条")
finally:
    db.close()
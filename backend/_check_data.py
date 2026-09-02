from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    tables = {
        'ods_stock_basic': 'ODS 股票基础',
        'ods_stock_daily': 'ODS 日线行情',
        'ods_daily_basic': 'ODS 每日指标',
        'ods_moneyflow': 'ODS 资金流向',
        'dwd_stock_daily': 'DWD 个股日度',
        'dwd_stock_info': 'DWD 股票信息',
        'dwd_financial_indicator': 'DWD 财务指标',
        'dws_stock_daily_wide': 'DWS 个股日宽',
        'dws_industry_daily': 'DWS 行业日度',
        'dws_stock_weekly': 'DWS 个股周度',
        'ads_stock_overview': 'ADS 个股总览',
        'ads_kline_data': 'ADS K线',
        'ads_technical_radar': 'ADS 技术雷达',
        'ads_capital_flow': 'ADS 资金流向',
        'ads_financial_health': 'ADS 财务健康',
    }
    for t, name in tables.items():
        try:
            cnt = db.execute(text(f"SELECT COUNT(1) FROM {t}")).scalar()
            print(f"  {name}: {cnt} 行")
        except Exception as e:
            print(f"  {name}: 错误 - {e}")
finally:
    db.close()
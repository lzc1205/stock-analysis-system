"""
ADS层（应用层）数据库模型
面向大屏的最终数据表
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, TIMESTAMP, Index, Integer, Text
from sqlalchemy.sql import func
from app.utils.database import Base


class AdsStockOverview(Base):
    """个股总览数据"""
    __tablename__ = "ads_stock_overview"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, unique=True, comment="股票代码")
    name = Column(String(50), comment="股票名称")
    industry = Column(String(50), comment="行业")
    latest_price = Column(DECIMAL(10, 3), comment="最新价")
    latest_pct_chg = Column(DECIMAL(10, 3), comment="最新涨跌幅")
    latest_vol = Column(DECIMAL(20, 2), comment="最新成交量")
    latest_amount = Column(DECIMAL(20, 2), comment="最新成交额")
    pe = Column(DECIMAL(10, 3), comment="市盈率")
    pb = Column(DECIMAL(10, 3), comment="市净率")
    total_mv = Column(DECIMAL(20, 2), comment="总市值(万元)")
    circ_mv = Column(DECIMAL(20, 2), comment="流通市值(万元)")
    ma5 = Column(DECIMAL(10, 3), comment="MA5")
    ma20 = Column(DECIMAL(10, 3), comment="MA20")
    dif = Column(DECIMAL(10, 3), comment="MACD DIF")
    dea = Column(DECIMAL(10, 3), comment="MACD DEA")
    rsi6 = Column(DECIMAL(10, 3), comment="RSI6")
    net_mf_vol = Column(DECIMAL(20, 2), comment="主力净流入")
    update_date = Column(Date, comment="更新日期")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("idx_ads_overview_industry", "industry"),
    )


class AdsKlineData(Base):
    """K线图数据"""
    __tablename__ = "ads_kline_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    open = Column(DECIMAL(10, 3), comment="开盘价")
    high = Column(DECIMAL(10, 3), comment="最高价")
    low = Column(DECIMAL(10, 3), comment="最低价")
    close = Column(DECIMAL(10, 3), comment="收盘价")
    vol = Column(DECIMAL(20, 2), comment="成交量(手)")
    amount = Column(DECIMAL(20, 2), comment="成交额(千元)")
    pct_chg = Column(DECIMAL(10, 3), comment="涨跌幅(%)")
    ma5 = Column(DECIMAL(10, 3), comment="MA5")
    ma10 = Column(DECIMAL(10, 3), comment="MA10")
    ma20 = Column(DECIMAL(10, 3), comment="MA20")
    ma60 = Column(DECIMAL(10, 3), comment="MA60")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ads_kline_ts_date", "ts_code", "trade_date", unique=True),
        Index("idx_ads_kline_date", "trade_date"),
    )


class AdsTechnicalRadar(Base):
    """技术指标雷达图数据"""
    __tablename__ = "ads_technical_radar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    trend_score = Column(DECIMAL(10, 3), comment="趋势评分(0-100)")
    momentum_score = Column(DECIMAL(10, 3), comment="动量评分(0-100)")
    volatility_score = Column(DECIMAL(10, 3), comment="波动评分(0-100)")
    volume_score = Column(DECIMAL(10, 3), comment="量能评分(0-100)")
    overall_score = Column(DECIMAL(10, 3), comment="综合评分(0-100)")
    signal = Column(String(10), comment="信号：买入/卖出/观望")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ads_radar_ts_date", "ts_code", "trade_date", unique=True),
    )


class AdsCapitalFlow(Base):
    """资金流向数据"""
    __tablename__ = "ads_capital_flow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    buy_sm = Column(DECIMAL(20, 2), comment="小单买入")
    sell_sm = Column(DECIMAL(20, 2), comment="小单卖出")
    buy_md = Column(DECIMAL(20, 2), comment="中单买入")
    sell_md = Column(DECIMAL(20, 2), comment="中单卖出")
    buy_lg = Column(DECIMAL(20, 2), comment="大单买入")
    sell_lg = Column(DECIMAL(20, 2), comment="大单卖出")
    buy_elg = Column(DECIMAL(20, 2), comment="超大单买入")
    sell_elg = Column(DECIMAL(20, 2), comment="超大单卖出")
    net_sm = Column(DECIMAL(20, 2), comment="小单净流入")
    net_md = Column(DECIMAL(20, 2), comment="中单净流入")
    net_lg = Column(DECIMAL(20, 2), comment="大单净流入")
    net_elg = Column(DECIMAL(20, 2), comment="超大单净流入")
    net_total = Column(DECIMAL(20, 2), comment="总净流入")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ads_flow_ts_date", "ts_code", "trade_date", unique=True),
    )


class AdsFinancialHealth(Base):
    """财务健康度评分"""
    __tablename__ = "ads_financial_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    end_date = Column(Date, nullable=False, comment="报告期")
    roe = Column(DECIMAL(10, 3), comment="ROE(%)")
    gross_margin = Column(DECIMAL(10, 3), comment="毛利率(%)")
    net_margin = Column(DECIMAL(10, 3), comment="净利率(%)")
    debt_ratio = Column(DECIMAL(10, 3), comment="资产负债率(%)")
    revenue_yoy = Column(DECIMAL(10, 3), comment="营收同比增长率(%)")
    n_income_yoy = Column(DECIMAL(10, 3), comment="净利润同比增长率(%)")
    eps = Column(DECIMAL(10, 4), comment="每股收益")
    health_score = Column(DECIMAL(10, 3), comment="健康度评分(0-100)")
    health_level = Column(String(20), comment="健康等级：优秀/良好/一般/较差")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ads_health_ts_date", "ts_code", "end_date", unique=True),
    )
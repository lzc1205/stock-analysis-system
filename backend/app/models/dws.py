"""
DWS层（汇总层）数据库模型
按主题聚合的宽表
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, TIMESTAMP, Index, Integer
from sqlalchemy.sql import func
from app.utils.database import Base


class DwsStockDailyWide(Base):
    """个股日度宽表：行情+基本面+资金流向+技术指标"""
    __tablename__ = "dws_stock_daily_wide"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    # 行情数据
    open = Column(DECIMAL(10, 3), comment="开盘价")
    high = Column(DECIMAL(10, 3), comment="最高价")
    low = Column(DECIMAL(10, 3), comment="最低价")
    close = Column(DECIMAL(10, 3), comment="收盘价")
    pre_close = Column(DECIMAL(10, 3), comment="昨收价")
    pct_chg = Column(DECIMAL(10, 3), comment="涨跌幅(%)")
    vol = Column(DECIMAL(20, 2), comment="成交量(手)")
    amount = Column(DECIMAL(20, 2), comment="成交额(千元)")
    turn = Column(DECIMAL(10, 3), comment="换手率(%)")
    # 技术指标
    ma5 = Column(DECIMAL(10, 3), comment="MA5")
    ma10 = Column(DECIMAL(10, 3), comment="MA10")
    ma20 = Column(DECIMAL(10, 3), comment="MA20")
    ma60 = Column(DECIMAL(10, 3), comment="MA60")
    dif = Column(DECIMAL(10, 3), comment="MACD DIF")
    dea = Column(DECIMAL(10, 3), comment="MACD DEA")
    macd_bar = Column(DECIMAL(10, 3), comment="MACD 柱")
    rsi6 = Column(DECIMAL(10, 3), comment="RSI6")
    rsi12 = Column(DECIMAL(10, 3), comment="RSI12")
    rsi24 = Column(DECIMAL(10, 3), comment="RSI24")
    k = Column(DECIMAL(10, 3), comment="KDJ K")
    d = Column(DECIMAL(10, 3), comment="KDJ D")
    j = Column(DECIMAL(10, 3), comment="KDJ J")
    # 资金流向
    net_mf_vol = Column(DECIMAL(20, 2), comment="主力净流入(万元)")
    # 基本面
    pe = Column(DECIMAL(10, 3), comment="市盈率")
    pb = Column(DECIMAL(10, 3), comment="市净率")
    total_mv = Column(DECIMAL(20, 2), comment="总市值(万元)")
    circ_mv = Column(DECIMAL(20, 2), comment="流通市值(万元)")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_dws_wide_ts_date", "ts_code", "trade_date", unique=True),
        Index("idx_dws_wide_date", "trade_date"),
    )


class DwsIndustryDaily(Base):
    """行业日度汇总"""
    __tablename__ = "dws_industry_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    industry_l1 = Column(String(50), nullable=False, comment="一级行业")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    stock_count = Column(Integer, comment="股票数量")
    rise_count = Column(Integer, comment="上涨家数")
    fall_count = Column(Integer, comment="下跌家数")
    avg_pct_chg = Column(DECIMAL(10, 3), comment="平均涨跌幅(%)")
    total_amount = Column(DECIMAL(20, 2), comment="总成交额(万元)")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_dws_industry_date", "industry_l1", "trade_date", unique=True),
    )


class DwsStockWeekly(Base):
    """个股周度汇总"""
    __tablename__ = "dws_stock_weekly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    week_start = Column(Date, nullable=False, comment="周起始日")
    week_end = Column(Date, nullable=False, comment="周结束日")
    open = Column(DECIMAL(10, 3), comment="周开盘价")
    high = Column(DECIMAL(10, 3), comment="周最高价")
    low = Column(DECIMAL(10, 3), comment="周最低价")
    close = Column(DECIMAL(10, 3), comment="周收盘价")
    pct_chg = Column(DECIMAL(10, 3), comment="周涨跌幅(%)")
    vol = Column(DECIMAL(20, 2), comment="周成交量")
    amount = Column(DECIMAL(20, 2), comment="周成交额")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_dws_weekly_ts_week", "ts_code", "week_start", unique=True),
    )
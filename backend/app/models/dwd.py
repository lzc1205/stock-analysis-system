"""
DWD层（明细层）数据库模型
清洗后的标准明细数据
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, TIMESTAMP, Index
from sqlalchemy.sql import func
from app.utils.database import Base


class DwdStockDaily(Base):
    """标准日线行情明细表"""
    __tablename__ = "dwd_stock_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    open = Column(DECIMAL(10, 3), comment="开盘价")
    high = Column(DECIMAL(10, 3), comment="最高价")
    low = Column(DECIMAL(10, 3), comment="最低价")
    close = Column(DECIMAL(10, 3), comment="收盘价")
    pre_close = Column(DECIMAL(10, 3), comment="昨收价")
    change = Column(DECIMAL(10, 3), comment="涨跌额")
    pct_chg = Column(DECIMAL(10, 3), comment="涨跌幅(%)")
    vol = Column(DECIMAL(20, 2), comment="成交量(手)")
    amount = Column(DECIMAL(20, 2), comment="成交额(千元)")
    turn = Column(DECIMAL(10, 3), comment="换手率(%)")
    amplitude = Column(DECIMAL(10, 3), comment="振幅(%)")
    is_st = Column(Integer, default=0, comment="是否ST 0=否 1=是")
    data_quality = Column(Integer, default=1, comment="数据质量 1=正常 0=异常")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_dwd_daily_ts_date", "ts_code", "trade_date", unique=True),
        Index("idx_dwd_daily_date", "trade_date"),
        Index("idx_dwd_daily_ts_code", "ts_code"),
    )


class DwdStockInfo(Base):
    """股票维度表"""
    __tablename__ = "dwd_stock_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, unique=True, comment="股票代码")
    symbol = Column(String(10), comment="交易代码")
    name = Column(String(50), comment="股票名称")
    area = Column(String(50), comment="地区")
    industry_l1 = Column(String(50), comment="一级行业")
    industry_l2 = Column(String(50), comment="二级行业")
    market = Column(String(20), comment="市场")
    list_date = Column(Date, comment="上市日期")
    is_st = Column(Integer, default=0, comment="是否ST")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_dwd_info_industry_l1", "industry_l1"),
    )


class DwdFinancialIndicator(Base):
    """财务指标明细表"""
    __tablename__ = "dwd_financial_indicator"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    end_date = Column(Date, nullable=False, comment="报告期")
    report_type = Column(String(10), comment="报表类型")
    revenue = Column(DECIMAL(20, 2), comment="营业收入")
    revenue_yoy = Column(DECIMAL(10, 3), comment="营收同比增长率(%)")
    n_income = Column(DECIMAL(20, 2), comment="净利润")
    n_income_yoy = Column(DECIMAL(10, 3), comment="净利润同比增长率(%)")
    eps = Column(DECIMAL(10, 4), comment="每股收益")
    roe = Column(DECIMAL(10, 3), comment="ROE(%)")
    gross_margin = Column(DECIMAL(10, 3), comment="毛利率(%)")
    net_margin = Column(DECIMAL(10, 3), comment="净利率(%)")
    debt_ratio = Column(DECIMAL(10, 3), comment="资产负债率(%)")
    total_assets = Column(DECIMAL(20, 2), comment="总资产")
    total_hldr_eqy = Column(DECIMAL(20, 2), comment="股东权益")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_dwd_fin_ts_rep", "ts_code", "end_date", "report_type", unique=True),
    )
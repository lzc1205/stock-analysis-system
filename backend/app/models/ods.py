"""
ODS层（贴源层）数据库模型
存储从数据源采集的原始数据
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, TIMESTAMP, Index, Text
from sqlalchemy.sql import func
from app.utils.database import Base


class OdsStockBasic(Base):
    """股票基本信息"""
    __tablename__ = "ods_stock_basic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    symbol = Column(String(10), comment="交易代码")
    name = Column(String(50), comment="股票名称")
    area = Column(String(50), comment="地区")
    industry = Column(String(50), comment="行业")
    market = Column(String(20), comment="市场类型")
    list_date = Column(Date, comment="上市日期")
    is_hs = Column(String(1), comment="是否沪深港通")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_basic_ts_code", "ts_code", unique=True),
        Index("idx_ods_basic_industry", "industry"),
    )


class OdsStockDaily(Base):
    """日线行情原始数据"""
    __tablename__ = "ods_stock_daily"

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
    source = Column(String(20), default="baostock", comment="数据来源")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_daily_ts_date", "ts_code", "trade_date", unique=True),
        Index("idx_ods_daily_date", "trade_date"),
        Index("idx_ods_daily_ts_code", "ts_code"),
    )


class OdsDailyBasic(Base):
    """每日基本面指标"""
    __tablename__ = "ods_daily_basic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    turnover_rate = Column(DECIMAL(10, 3), comment="换手率(%)")
    pe = Column(DECIMAL(10, 3), comment="市盈率")
    pb = Column(DECIMAL(10, 3), comment="市净率")
    total_mv = Column(DECIMAL(20, 2), comment="总市值(万元)")
    circ_mv = Column(DECIMAL(20, 2), comment="流通市值(万元)")
    source = Column(String(20), default="baostock", comment="数据来源")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_daily_basic_ts_date", "ts_code", "trade_date", unique=True),
        Index("idx_ods_daily_basic_date", "trade_date"),
    )


class OdsMoneyFlow(Base):
    """资金流向原始数据"""
    __tablename__ = "ods_moneyflow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    buy_sm_vol = Column(DECIMAL(20, 2), comment="小单买入量")
    sell_sm_vol = Column(DECIMAL(20, 2), comment="小单卖出量")
    buy_md_vol = Column(DECIMAL(20, 2), comment="中单买入量")
    sell_md_vol = Column(DECIMAL(20, 2), comment="中单卖出量")
    buy_lg_vol = Column(DECIMAL(20, 2), comment="大单买入量")
    sell_lg_vol = Column(DECIMAL(20, 2), comment="大单卖出量")
    buy_elg_vol = Column(DECIMAL(20, 2), comment="超大单买入量")
    sell_elg_vol = Column(DECIMAL(20, 2), comment="超大单卖出量")
    net_mf_vol = Column(DECIMAL(20, 2), comment="主力净流入")
    source = Column(String(20), default="akshare", comment="数据来源")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_flow_ts_date", "ts_code", "trade_date", unique=True),
        Index("idx_ods_flow_date", "trade_date"),
    )


class OdsIncome(Base):
    """利润表原始数据"""
    __tablename__ = "ods_income"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    ann_date = Column(Date, comment="公告日期")
    f_ann_date = Column(Date, comment="实际公告日期")
    end_date = Column(Date, comment="报告期")
    report_type = Column(String(10), comment="报表类型")
    revenue = Column(DECIMAL(20, 2), comment="营业总收入")
    total_cogs = Column(DECIMAL(20, 2), comment="营业总成本")
    operate_profit = Column(DECIMAL(20, 2), comment="营业利润")
    total_profit = Column(DECIMAL(20, 2), comment="利润总额")
    n_income = Column(DECIMAL(20, 2), comment="净利润")
    eps = Column(DECIMAL(10, 4), comment="每股收益")
    source = Column(String(20), default="baostock", comment="数据来源")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_income_ts_rep", "ts_code", "end_date", "report_type", unique=True),
    )


class OdsBalanceSheet(Base):
    """资产负债表原始数据"""
    __tablename__ = "ods_balancesheet"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    ann_date = Column(Date, comment="公告日期")
    f_ann_date = Column(Date, comment="实际公告日期")
    end_date = Column(Date, comment="报告期")
    report_type = Column(String(10), comment="报表类型")
    total_assets = Column(DECIMAL(20, 2), comment="总资产")
    total_liab = Column(DECIMAL(20, 2), comment="总负债")
    total_hldr_eqy = Column(DECIMAL(20, 2), comment="股东权益合计")
    source = Column(String(20), default="baostock", comment="数据来源")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_bs_ts_rep", "ts_code", "end_date", "report_type", unique=True),
    )


class OdsCashFlow(Base):
    """现金流量表原始数据"""
    __tablename__ = "ods_cashflow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment="股票代码")
    ann_date = Column(Date, comment="公告日期")
    f_ann_date = Column(Date, comment="实际公告日期")
    end_date = Column(Date, comment="报告期")
    report_type = Column(String(10), comment="报表类型")
    n_cashflow_act = Column(DECIMAL(20, 2), comment="经营活动现金流量净额")
    n_cashflow_inv = Column(DECIMAL(20, 2), comment="投资活动现金流量净额")
    n_cashflow_fin = Column(DECIMAL(20, 2), comment="筹资活动现金流量净额")
    source = Column(String(20), default="baostock", comment="数据来源")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index("uk_ods_cf_ts_rep", "ts_code", "end_date", "report_type", unique=True),
    )
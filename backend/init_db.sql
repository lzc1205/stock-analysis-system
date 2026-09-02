-- 个股金融数据仓库初始化脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock_warehouse
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE stock_warehouse;

-- ==================== ODS 层（贴源层） ====================

CREATE TABLE IF NOT EXISTS ods_stock_basic (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  symbol VARCHAR(10) COMMENT '交易代码',
  name VARCHAR(50) COMMENT '股票名称',
  area VARCHAR(50) COMMENT '地区',
  industry VARCHAR(50) COMMENT '行业',
  market VARCHAR(20) COMMENT '市场类型',
  list_date DATE COMMENT '上市日期',
  is_hs VARCHAR(1) COMMENT '是否沪深港通',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_basic_ts_code (ts_code),
  KEY idx_ods_basic_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-股票基本信息';

CREATE TABLE IF NOT EXISTS ods_stock_daily (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  open DECIMAL(10,3) COMMENT '开盘价',
  high DECIMAL(10,3) COMMENT '最高价',
  low DECIMAL(10,3) COMMENT '最低价',
  close DECIMAL(10,3) COMMENT '收盘价',
  pre_close DECIMAL(10,3) COMMENT '昨收价',
  `change` DECIMAL(10,3) COMMENT '涨跌额',
  pct_chg DECIMAL(10,3) COMMENT '涨跌幅(%)',
  vol DECIMAL(20,2) COMMENT '成交量(手)',
  amount DECIMAL(20,2) COMMENT '成交额(千元)',
  turn DECIMAL(10,3) COMMENT '换手率(%)',
  source VARCHAR(20) DEFAULT 'baostock' COMMENT '数据来源',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_daily_ts_date (ts_code, trade_date),
  KEY idx_ods_daily_date (trade_date),
  KEY idx_ods_daily_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-日线行情原始数据';

CREATE TABLE IF NOT EXISTS ods_daily_basic (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  turnover_rate DECIMAL(10,3) COMMENT '换手率(%)',
  pe DECIMAL(10,3) COMMENT '市盈率',
  pb DECIMAL(10,3) COMMENT '市净率',
  total_mv DECIMAL(20,2) COMMENT '总市值(万元)',
  circ_mv DECIMAL(20,2) COMMENT '流通市值(万元)',
  source VARCHAR(20) DEFAULT 'baostock' COMMENT '数据来源',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_daily_basic_ts_date (ts_code, trade_date),
  KEY idx_ods_daily_basic_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-每日基本面指标';

CREATE TABLE IF NOT EXISTS ods_moneyflow (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  buy_sm_vol DECIMAL(20,2) COMMENT '小单买入量',
  sell_sm_vol DECIMAL(20,2) COMMENT '小单卖出量',
  buy_md_vol DECIMAL(20,2) COMMENT '中单买入量',
  sell_md_vol DECIMAL(20,2) COMMENT '中单卖出量',
  buy_lg_vol DECIMAL(20,2) COMMENT '大单买入量',
  sell_lg_vol DECIMAL(20,2) COMMENT '大单卖出量',
  buy_elg_vol DECIMAL(20,2) COMMENT '超大单买入量',
  sell_elg_vol DECIMAL(20,2) COMMENT '超大单卖出量',
  net_mf_vol DECIMAL(20,2) COMMENT '主力净流入',
  source VARCHAR(20) DEFAULT 'akshare' COMMENT '数据来源',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_flow_ts_date (ts_code, trade_date),
  KEY idx_ods_flow_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-资金流向原始数据';

CREATE TABLE IF NOT EXISTS ods_income (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  ann_date DATE COMMENT '公告日期',
  f_ann_date DATE COMMENT '实际公告日期',
  end_date DATE COMMENT '报告期',
  report_type VARCHAR(10) COMMENT '报表类型',
  revenue DECIMAL(20,2) COMMENT '营业总收入',
  total_cogs DECIMAL(20,2) COMMENT '营业总成本',
  operate_profit DECIMAL(20,2) COMMENT '营业利润',
  total_profit DECIMAL(20,2) COMMENT '利润总额',
  n_income DECIMAL(20,2) COMMENT '净利润',
  eps DECIMAL(10,4) COMMENT '每股收益',
  source VARCHAR(20) DEFAULT 'baostock' COMMENT '数据来源',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_income_ts_rep (ts_code, end_date, report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-利润表原始数据';

CREATE TABLE IF NOT EXISTS ods_balancesheet (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  ann_date DATE COMMENT '公告日期',
  f_ann_date DATE COMMENT '实际公告日期',
  end_date DATE COMMENT '报告期',
  report_type VARCHAR(10) COMMENT '报表类型',
  total_assets DECIMAL(20,2) COMMENT '总资产',
  total_liab DECIMAL(20,2) COMMENT '总负债',
  total_hldr_eqy DECIMAL(20,2) COMMENT '股东权益合计',
  source VARCHAR(20) DEFAULT 'baostock' COMMENT '数据来源',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_bs_ts_rep (ts_code, end_date, report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-资产负债表原始数据';

CREATE TABLE IF NOT EXISTS ods_cashflow (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  ann_date DATE COMMENT '公告日期',
  f_ann_date DATE COMMENT '实际公告日期',
  end_date DATE COMMENT '报告期',
  report_type VARCHAR(10) COMMENT '报表类型',
  n_cashflow_act DECIMAL(20,2) COMMENT '经营活动现金流量净额',
  n_cashflow_inv DECIMAL(20,2) COMMENT '投资活动现金流量净额',
  n_cashflow_fin DECIMAL(20,2) COMMENT '筹资活动现金流量净额',
  source VARCHAR(20) DEFAULT 'baostock' COMMENT '数据来源',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ods_cf_ts_rep (ts_code, end_date, report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS-现金流量表原始数据';

-- ==================== DWD 层（明细层） ====================

CREATE TABLE IF NOT EXISTS dwd_stock_daily (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  open DECIMAL(10,3) COMMENT '开盘价',
  high DECIMAL(10,3) COMMENT '最高价',
  low DECIMAL(10,3) COMMENT '最低价',
  close DECIMAL(10,3) COMMENT '收盘价',
  pre_close DECIMAL(10,3) COMMENT '昨收价',
  `change` DECIMAL(10,3) COMMENT '涨跌额',
  pct_chg DECIMAL(10,3) COMMENT '涨跌幅(%)',
  vol DECIMAL(20,2) COMMENT '成交量(手)',
  amount DECIMAL(20,2) COMMENT '成交额(千元)',
  turn DECIMAL(10,3) COMMENT '换手率(%)',
  amplitude DECIMAL(10,3) COMMENT '振幅(%)',
  is_st INT DEFAULT 0 COMMENT '是否ST 0=否 1=是',
  data_quality INT DEFAULT 1 COMMENT '数据质量 1=正常 0=异常',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_dwd_daily_ts_date (ts_code, trade_date),
  KEY idx_dwd_daily_date (trade_date),
  KEY idx_dwd_daily_ts_code (ts_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD-标准日线行情明细表';

CREATE TABLE IF NOT EXISTS dwd_stock_info (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL UNIQUE COMMENT '股票代码',
  symbol VARCHAR(10) COMMENT '交易代码',
  name VARCHAR(50) COMMENT '股票名称',
  area VARCHAR(50) COMMENT '地区',
  industry_l1 VARCHAR(50) COMMENT '一级行业',
  industry_l2 VARCHAR(50) COMMENT '二级行业',
  market VARCHAR(20) COMMENT '市场',
  list_date DATE COMMENT '上市日期',
  is_st INT DEFAULT 0 COMMENT '是否ST',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_dwd_info_industry_l1 (industry_l1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD-股票维度表';

CREATE TABLE IF NOT EXISTS dwd_financial_indicator (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  end_date DATE NOT NULL COMMENT '报告期',
  report_type VARCHAR(10) COMMENT '报表类型',
  revenue DECIMAL(20,2) COMMENT '营业收入',
  revenue_yoy DECIMAL(10,3) COMMENT '营收同比增长率(%)',
  n_income DECIMAL(20,2) COMMENT '净利润',
  n_income_yoy DECIMAL(10,3) COMMENT '净利润同比增长率(%)',
  eps DECIMAL(10,4) COMMENT '每股收益',
  roe DECIMAL(10,3) COMMENT 'ROE(%)',
  gross_margin DECIMAL(10,3) COMMENT '毛利率(%)',
  net_margin DECIMAL(10,3) COMMENT '净利率(%)',
  debt_ratio DECIMAL(10,3) COMMENT '资产负债率(%)',
  total_assets DECIMAL(20,2) COMMENT '总资产',
  total_hldr_eqy DECIMAL(20,2) COMMENT '股东权益',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_dwd_fin_ts_rep (ts_code, end_date, report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD-财务指标明细表';

-- ==================== DWS 层（汇总层） ====================

CREATE TABLE IF NOT EXISTS dws_stock_daily_wide (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  open DECIMAL(10,3) COMMENT '开盘价',
  high DECIMAL(10,3) COMMENT '最高价',
  low DECIMAL(10,3) COMMENT '最低价',
  close DECIMAL(10,3) COMMENT '收盘价',
  pre_close DECIMAL(10,3) COMMENT '昨收价',
  pct_chg DECIMAL(10,3) COMMENT '涨跌幅(%)',
  vol DECIMAL(20,2) COMMENT '成交量(手)',
  amount DECIMAL(20,2) COMMENT '成交额(千元)',
  turn DECIMAL(10,3) COMMENT '换手率(%)',
  ma5 DECIMAL(10,3) COMMENT 'MA5',
  ma10 DECIMAL(10,3) COMMENT 'MA10',
  ma20 DECIMAL(10,3) COMMENT 'MA20',
  ma60 DECIMAL(10,3) COMMENT 'MA60',
  dif DECIMAL(10,3) COMMENT 'MACD DIF',
  dea DECIMAL(10,3) COMMENT 'MACD DEA',
  macd_bar DECIMAL(10,3) COMMENT 'MACD 柱',
  rsi6 DECIMAL(10,3) COMMENT 'RSI6',
  rsi12 DECIMAL(10,3) COMMENT 'RSI12',
  rsi24 DECIMAL(10,3) COMMENT 'RSI24',
  k DECIMAL(10,3) COMMENT 'KDJ K',
  d DECIMAL(10,3) COMMENT 'KDJ D',
  j DECIMAL(10,3) COMMENT 'KDJ J',
  net_mf_vol DECIMAL(20,2) COMMENT '主力净流入(万元)',
  pe DECIMAL(10,3) COMMENT '市盈率',
  pb DECIMAL(10,3) COMMENT '市净率',
  total_mv DECIMAL(20,2) COMMENT '总市值(万元)',
  circ_mv DECIMAL(20,2) COMMENT '流通市值(万元)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_dws_wide_ts_date (ts_code, trade_date),
  KEY idx_dws_wide_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS-个股日度宽表';

CREATE TABLE IF NOT EXISTS dws_industry_daily (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  industry_l1 VARCHAR(50) NOT NULL COMMENT '一级行业',
  trade_date DATE NOT NULL COMMENT '交易日期',
  stock_count INT COMMENT '股票数量',
  rise_count INT COMMENT '上涨家数',
  fall_count INT COMMENT '下跌家数',
  avg_pct_chg DECIMAL(10,3) COMMENT '平均涨跌幅(%)',
  total_amount DECIMAL(20,2) COMMENT '总成交额(万元)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_dws_industry_date (industry_l1, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS-行业日度汇总';

CREATE TABLE IF NOT EXISTS dws_stock_weekly (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  week_start DATE NOT NULL COMMENT '周起始日',
  week_end DATE NOT NULL COMMENT '周结束日',
  open DECIMAL(10,3) COMMENT '周开盘价',
  high DECIMAL(10,3) COMMENT '周最高价',
  low DECIMAL(10,3) COMMENT '周最低价',
  close DECIMAL(10,3) COMMENT '周收盘价',
  pct_chg DECIMAL(10,3) COMMENT '周涨跌幅(%)',
  vol DECIMAL(20,2) COMMENT '周成交量',
  amount DECIMAL(20,2) COMMENT '周成交额',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_dws_weekly_ts_week (ts_code, week_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS-个股周度汇总';

-- ==================== ADS 层（应用层） ====================

CREATE TABLE IF NOT EXISTS ads_stock_overview (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL UNIQUE COMMENT '股票代码',
  name VARCHAR(50) COMMENT '股票名称',
  industry VARCHAR(50) COMMENT '行业',
  latest_price DECIMAL(10,3) COMMENT '最新价',
  latest_pct_chg DECIMAL(10,3) COMMENT '最新涨跌幅',
  latest_vol DECIMAL(20,2) COMMENT '最新成交量',
  latest_amount DECIMAL(20,2) COMMENT '最新成交额',
  pe DECIMAL(10,3) COMMENT '市盈率',
  pb DECIMAL(10,3) COMMENT '市净率',
  total_mv DECIMAL(20,2) COMMENT '总市值(万元)',
  circ_mv DECIMAL(20,2) COMMENT '流通市值(万元)',
  ma5 DECIMAL(10,3) COMMENT 'MA5',
  ma20 DECIMAL(10,3) COMMENT 'MA20',
  dif DECIMAL(10,3) COMMENT 'MACD DIF',
  dea DECIMAL(10,3) COMMENT 'MACD DEA',
  rsi6 DECIMAL(10,3) COMMENT 'RSI6',
  net_mf_vol DECIMAL(20,2) COMMENT '主力净流入',
  update_date DATE COMMENT '更新日期',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_ads_overview_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS-个股总览数据';

CREATE TABLE IF NOT EXISTS ads_kline_data (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  open DECIMAL(10,3) COMMENT '开盘价',
  high DECIMAL(10,3) COMMENT '最高价',
  low DECIMAL(10,3) COMMENT '最低价',
  close DECIMAL(10,3) COMMENT '收盘价',
  vol DECIMAL(20,2) COMMENT '成交量(手)',
  amount DECIMAL(20,2) COMMENT '成交额(千元)',
  pct_chg DECIMAL(10,3) COMMENT '涨跌幅(%)',
  ma5 DECIMAL(10,3) COMMENT 'MA5',
  ma10 DECIMAL(10,3) COMMENT 'MA10',
  ma20 DECIMAL(10,3) COMMENT 'MA20',
  ma60 DECIMAL(10,3) COMMENT 'MA60',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ads_kline_ts_date (ts_code, trade_date),
  KEY idx_ads_kline_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS-K线图数据';

CREATE TABLE IF NOT EXISTS ads_technical_radar (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  trend_score DECIMAL(10,3) COMMENT '趋势评分(0-100)',
  momentum_score DECIMAL(10,3) COMMENT '动量评分(0-100)',
  volatility_score DECIMAL(10,3) COMMENT '波动评分(0-100)',
  volume_score DECIMAL(10,3) COMMENT '量能评分(0-100)',
  overall_score DECIMAL(10,3) COMMENT '综合评分(0-100)',
  signal VARCHAR(10) COMMENT '信号：买入/卖出/观望',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ads_radar_ts_date (ts_code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS-技术指标雷达图数据';

CREATE TABLE IF NOT EXISTS ads_capital_flow (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  buy_sm DECIMAL(20,2) COMMENT '小单买入',
  sell_sm DECIMAL(20,2) COMMENT '小单卖出',
  buy_md DECIMAL(20,2) COMMENT '中单买入',
  sell_md DECIMAL(20,2) COMMENT '中单卖出',
  buy_lg DECIMAL(20,2) COMMENT '大单买入',
  sell_lg DECIMAL(20,2) COMMENT '大单卖出',
  buy_elg DECIMAL(20,2) COMMENT '超大单买入',
  sell_elg DECIMAL(20,2) COMMENT '超大单卖出',
  net_sm DECIMAL(20,2) COMMENT '小单净流入',
  net_md DECIMAL(20,2) COMMENT '中单净流入',
  net_lg DECIMAL(20,2) COMMENT '大单净流入',
  net_elg DECIMAL(20,2) COMMENT '超大单净流入',
  net_total DECIMAL(20,2) COMMENT '总净流入',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ads_flow_ts_date (ts_code, trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS-资金流向数据';

CREATE TABLE IF NOT EXISTS ads_financial_health (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
  end_date DATE NOT NULL COMMENT '报告期',
  roe DECIMAL(10,3) COMMENT 'ROE(%)',
  gross_margin DECIMAL(10,3) COMMENT '毛利率(%)',
  net_margin DECIMAL(10,3) COMMENT '净利率(%)',
  debt_ratio DECIMAL(10,3) COMMENT '资产负债率(%)',
  revenue_yoy DECIMAL(10,3) COMMENT '营收同比增长率(%)',
  n_income_yoy DECIMAL(10,3) COMMENT '净利润同比增长率(%)',
  eps DECIMAL(10,4) COMMENT '每股收益',
  health_score DECIMAL(10,3) COMMENT '健康度评分(0-100)',
  health_level VARCHAR(20) COMMENT '健康等级：优秀/良好/一般/较差',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ads_health_ts_date (ts_code, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ADS-财务健康度评分';
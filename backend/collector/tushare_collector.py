"""
Tushare 数据采集器（可选补充数据源）
需要注册获取 token，数据质量更高，但需积分
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
from app.utils.logger import logger


class TushareCollector:
    def __init__(self):
        self.api = None
        self._init_api()

    def _init_api(self):
        if not settings.tushare_token:
            logger.warning("Tushare token 未配置，Tushare 采集器不可用")
            return
        try:
            import tushare as ts
            ts.set_token(settings.tushare_token)
            self.api = ts.pro_api()
            logger.info("Tushare API 初始化成功")
        except ImportError:
            logger.warning("tushare 库未安装，跳过 Tushare 初始化")
        except Exception as e:
            logger.error(f"Tushare API 初始化失败: {e}")

    @property
    def is_available(self) -> bool:
        return self.api is not None

    def get_daily_kline(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取个股日线行情"""
        if not self.is_available:
            return pd.DataFrame()

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        try:
            df = self.api.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            if not df.empty:
                df["source"] = "tushare"
            logger.info(f"Tushare 获取 {ts_code} 日线行情成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取 {ts_code} 日线行情异常: {e}")
            return pd.DataFrame()

    def get_stock_basic(self, exchange: str = "") -> pd.DataFrame:
        """获取股票基本信息"""
        if not self.is_available:
            return pd.DataFrame()

        try:
            df = self.api.stock_basic(
                exchange=exchange,
                list_status="L",
                fields="ts_code,symbol,name,area,industry,market,list_date,is_hs",
            )
            logger.info(f"Tushare 获取股票基本信息成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取股票基本信息异常: {e}")
            return pd.DataFrame()

    def get_daily_basic(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取每日基本面指标"""
        if not self.is_available:
            return pd.DataFrame()

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        try:
            df = self.api.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields="ts_code,trade_date,turnover_rate,pe,pb,total_mv,circ_mv",
            )
            if not df.empty:
                df["source"] = "tushare"
            logger.info(f"Tushare 获取 {ts_code} 每日基本面成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取 {ts_code} 每日基本面异常: {e}")
            return pd.DataFrame()

    def get_moneyflow(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取个股资金流向"""
        if not self.is_available:
            return pd.DataFrame()

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        try:
            df = self.api.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            if not df.empty:
                df["source"] = "tushare"
            logger.info(f"Tushare 获取 {ts_code} 资金流向成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取 {ts_code} 资金流向异常: {e}")
            return pd.DataFrame()

    def get_income(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取利润表"""
        if not self.is_available:
            return pd.DataFrame()

        try:
            df = self.api.income(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            logger.info(f"Tushare 获取 {ts_code} 利润表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取 {ts_code} 利润表异常: {e}")
            return pd.DataFrame()

    def get_balancesheet(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取资产负债表"""
        if not self.is_available:
            return pd.DataFrame()

        try:
            df = self.api.balancesheet(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            logger.info(f"Tushare 获取 {ts_code} 资产负债表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取 {ts_code} 资产负债表异常: {e}")
            return pd.DataFrame()

    def get_cashflow(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """获取现金流量表"""
        if not self.is_available:
            return pd.DataFrame()

        try:
            df = self.api.cashflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            logger.info(f"Tushare 获取 {ts_code} 现金流量表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"Tushare 获取 {ts_code} 现金流量表异常: {e}")
            return pd.DataFrame()
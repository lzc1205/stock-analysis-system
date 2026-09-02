"""
AkShare 数据采集器（主数据源）
完全免费，开源多源聚合，作为 Baostock 的补充
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from app.utils.logger import logger


class AkShareCollector:
    def __init__(self):
        pass

    def _convert_code(self, ts_code: str) -> str:
        """将 ts_code 转换为 AkShare 格式
        600000.SH -> 600000
        """
        if "." in ts_code:
            return ts_code.split(".")[0]
        return ts_code

    def get_daily_hist(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取个股日线行情（东方财富源）
        :param ts_code: 股票代码，如 600000.SH
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :param period: daily, weekly, monthly
        :param adjust: qfq=前复权, hfq=后复权, 空=不复权
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        symbol = self._convert_code(ts_code)

        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            if not df.empty:
                df["ts_code"] = ts_code
                df["source"] = "akshare"
                df.rename(
                    columns={
                        "日期": "trade_date",
                        "开盘": "open",
                        "收盘": "close",
                        "最高": "high",
                        "最低": "low",
                        "成交量": "vol",
                        "成交额": "amount",
                        "振幅": "amplitude",
                        "涨跌幅": "pct_chg",
                        "涨跌额": "change",
                        "换手率": "turn",
                    },
                    inplace=True,
                )
            logger.info(f"AkShare 获取 {ts_code} 日线行情成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"AkShare 获取 {ts_code} 日线行情异常: {e}")
            return pd.DataFrame()

    def get_money_flow(self, ts_code: str, market: str = None) -> pd.DataFrame:
        """
        获取个股资金流向
        :param ts_code: 股票代码，如 600000.SH
        :param market: sh 或 sz
        """
        if market is None:
            market = ts_code.split(".")[1].lower() if "." in ts_code else "sh"

        symbol = self._convert_code(ts_code)

        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
            if not df.empty:
                df["ts_code"] = ts_code
                df["source"] = "akshare"
            logger.info(f"AkShare 获取 {ts_code} 资金流向成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"AkShare 获取 {ts_code} 资金流向异常: {e}")
            return pd.DataFrame()

    def get_financial_indicator(self, ts_code: str) -> pd.DataFrame:
        """获取财务指标数据"""
        symbol = self._convert_code(ts_code)

        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            if not df.empty:
                df["ts_code"] = ts_code
                df["source"] = "akshare"
            logger.info(f"AkShare 获取 {ts_code} 财务指标成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"AkShare 获取 {ts_code} 财务指标异常: {e}")
            return pd.DataFrame()

    def get_stock_list(self) -> pd.DataFrame:
        """获取全部A股列表"""
        try:
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                df.rename(
                    columns={
                        "代码": "symbol",
                        "名称": "name",
                        "最新价": "close",
                        "涨跌幅": "pct_chg",
                        "涨跌额": "change",
                        "成交量": "vol",
                        "成交额": "amount",
                        "今开": "open",
                        "最高": "high",
                        "最低": "low",
                        "昨收": "pre_close",
                    },
                    inplace=True,
                )
            logger.info(f"AkShare 获取A股列表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"AkShare 获取A股列表异常: {e}")
            return pd.DataFrame()

    def get_industry_stocks(self) -> pd.DataFrame:
        """获取行业板块股票"""
        try:
            df = ak.stock_board_industry_name_em()
            logger.info(f"AkShare 获取行业板块成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"AkShare 获取行业板块异常: {e}")
            return pd.DataFrame()
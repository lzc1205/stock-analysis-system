"""
Baostock 数据采集器（主数据源）
完全免费，无需注册，A股行情/财务数据
"""
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from app.utils.logger import logger


class BaostockCollector:
    def __init__(self):
        self.logged_in = False

    def login(self) -> bool:
        try:
            lg = bs.login()
            if lg.error_code == "0":
                self.logged_in = True
                logger.info("Baostock 登录成功")
                return True
            logger.error(f"Baostock 登录失败: {lg.error_msg}")
            return False
        except Exception as e:
            logger.error(f"Baostock 登录异常: {e}")
            return False

    def logout(self):
        if self.logged_in:
            bs.logout()
            self.logged_in = False
            logger.info("Baostock 已登出")

    def _ensure_login(self):
        if not self.logged_in:
            return self.login()
        return True

    def _convert_code(self, ts_code: str) -> str:
        """将 ts_code 格式转换为 baostock 格式
        600000.SH -> sh.600000
        000001.SZ -> sz.000001
        """
        if "." in ts_code:
            code, market = ts_code.split(".")
            return f"{market.lower()}.{code}"
        return ts_code

    def get_stock_basic(self) -> pd.DataFrame:
        """获取所有股票基本信息"""
        if not self._ensure_login():
            return pd.DataFrame()

        try:
            rs = bs.query_stock_basic()
            if rs.error_code != "0":
                logger.error(f"获取股票基本信息失败: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            logger.info(f"获取股票基本信息成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取股票基本信息异常: {e}")
            return pd.DataFrame()

    def get_daily_kline(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
        frequency: str = "d",
        adjust: str = "2",
    ) -> pd.DataFrame:
        """
        获取个股日线行情
        :param ts_code: 股票代码，如 600000.SH
        :param start_date: 开始日期 YYYY-MM-DD
        :param end_date: 结束日期 YYYY-MM-DD
        :param frequency: d=日线, w=周线, m=月线, 5/15/30/60=分钟线
        :param adjust: 1=后复权, 2=前复权, 3=不复权
        """
        if not self._ensure_login():
            return pd.DataFrame()

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        baostock_code = self._convert_code(ts_code)

        try:
            fields = "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg,isST"
            rs = bs.query_history_k_data_plus(
                baostock_code,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjust,
            )

            if rs.error_code != "0":
                logger.error(f"获取 {ts_code} 日线行情失败: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            if not df.empty:
                df.columns = df.columns.str.lower()
                df.rename(
                    columns={
                        "date": "trade_date",
                        "preclose": "pre_close",
                        "pctchg": "pct_chg",
                        "volume": "vol",
                        "isst": "is_st",
                    },
                    inplace=True,
                )
                df["ts_code"] = ts_code
                df["source"] = "baostock"
            logger.info(f"获取 {ts_code} 日线行情成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取 {ts_code} 日线行情异常: {e}")
            return pd.DataFrame()

    def get_profit_data(
        self, ts_code: str, start_year: int = None, end_year: int = None
    ) -> pd.DataFrame:
        """获取利润表数据"""
        if not self._ensure_login():
            return pd.DataFrame()

        if start_year is None:
            start_year = datetime.now().year - 5
        if end_year is None:
            end_year = datetime.now().year

        baostock_code = self._convert_code(ts_code)

        try:
            rs = bs.query_profit_data(
                code=baostock_code, year=start_year, quarter=4
            )
            if rs.error_code != "0":
                logger.error(f"获取 {ts_code} 利润表失败: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            if not df.empty:
                df["ts_code"] = ts_code
                df["source"] = "baostock"
            logger.info(f"获取 {ts_code} 利润表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取 {ts_code} 利润表异常: {e}")
            return pd.DataFrame()

    def get_balance_data(
        self, ts_code: str, start_year: int = None, end_year: int = None
    ) -> pd.DataFrame:
        """获取资产负债表数据"""
        if not self._ensure_login():
            return pd.DataFrame()

        if start_year is None:
            start_year = datetime.now().year - 5
        if end_year is None:
            end_year = datetime.now().year

        baostock_code = self._convert_code(ts_code)

        try:
            rs = bs.query_balance_data(
                code=baostock_code, year=start_year, quarter=4
            )
            if rs.error_code != "0":
                logger.error(f"获取 {ts_code} 资产负债表失败: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            if not df.empty:
                df["ts_code"] = ts_code
                df["source"] = "baostock"
            logger.info(f"获取 {ts_code} 资产负债表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取 {ts_code} 资产负债表异常: {e}")
            return pd.DataFrame()

    def get_cash_flow_data(
        self, ts_code: str, start_year: int = None, end_year: int = None
    ) -> pd.DataFrame:
        """获取现金流量表数据"""
        if not self._ensure_login():
            return pd.DataFrame()

        if start_year is None:
            start_year = datetime.now().year - 5
        if end_year is None:
            end_year = datetime.now().year

        baostock_code = self._convert_code(ts_code)

        try:
            rs = bs.query_cash_flow_data(
                code=baostock_code, year=start_year, quarter=4
            )
            if rs.error_code != "0":
                logger.error(f"获取 {ts_code} 现金流量表失败: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            if not df.empty:
                df["ts_code"] = ts_code
                df["source"] = "baostock"
            logger.info(f"获取 {ts_code} 现金流量表成功，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取 {ts_code} 现金流量表异常: {e}")
            return pd.DataFrame()
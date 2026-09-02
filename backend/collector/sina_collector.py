"""
新浪财经数据采集器
纯 HTTP REST API，无状态，支持多线程
"""
import requests
import pandas as pd
import time
from typing import List, Dict, Optional
from app.utils.logger import logger


class SinaCollector:
    """新浪财经数据采集器"""

    BASE_URL = "http://money.finance.sina.com.cn"
    LIST_URL = f"{BASE_URL}/d/api/openapi_proxy.php"
    KLINE_URL = f"{BASE_URL}/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.sina.com.cn",
        })

    def _prefix(self, ts_code: str) -> str:
        """600000.SH → sh600000  000001.SZ → sz000001"""
        code, market = ts_code.split(".")
        return f"{market.lower()}{code}"

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取全部A股列表（分页获取）
        返回: DataFrame with columns: ts_code, name, symbol, market
        """
        try:
            import urllib.parse
            import json
            all_stocks = {}
            page_size = 60
            page = 0

            while True:
                _s = json.dumps([["hq", "hs_a", "", 0, page, page_size]])
                url = f"{self.LIST_URL}?__s={urllib.parse.quote(_s)}"
                r = self.session.get(url, timeout=15)
                data = r.json()
                items = data[0]["items"]
                if not items:
                    break

                for item in items:
                    symbol = item[0]
                    code = item[1]
                    name = item[2]
                    market = symbol[:2].upper()
                    ts_code = f"{code}.{market}"
                    if ts_code not in all_stocks:
                        all_stocks[ts_code] = {
                            "ts_code": ts_code,
                            "name": name,
                            "symbol": code,
                            "market": market,
                        }

                if len(items) < page_size:
                    break
                page += 1
                if page == 1:
                    page = 2  # 跳过重复页

            stocks = list(all_stocks.values())
            df = pd.DataFrame(stocks)
            logger.info(f"新浪获取股票列表: {len(df)} 只")
            return df

        except Exception as e:
            logger.error(f"新浪获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_daily_kline(
        self, ts_code: str, start_date: str = None, end_date: str = None, datalen: int = 365
    ) -> pd.DataFrame:
        """
        获取日K线数据
        ts_code: 600000.SH / 000001.SZ
        """
        try:
            prefix = self._prefix(ts_code)
            params = {
                "symbol": prefix,
                "scale": 240,
                "ma": "no",
                "datalen": datalen,
            }
            r = self.session.get(self.KLINE_URL, params=params, timeout=10)
            data = r.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df.rename(columns={
                "day": "trade_date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "vol",
            }, inplace=True)

            df["ts_code"] = ts_code

            # 先转数值
            for col in ["open", "high", "low", "close", "vol"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df["pre_close"] = df["close"].shift(1)
            df["change"] = df["close"] - df["pre_close"]
            df["pct_chg"] = ((df["close"] - df["pre_close"]) / df["pre_close"].replace(0, None) * 100).round(3)
            df["amount"] = 0.0
            df["turn"] = 0.0
            df["pre_close"] = df["pre_close"].fillna(df["open"])
            df["change"] = df["change"].fillna(0)
            df["pct_chg"] = df["pct_chg"].fillna(0)

            cols = ["ts_code", "trade_date", "open", "high", "low", "close",
                    "pre_close", "change", "pct_chg", "vol", "amount", "turn"]
            df = df[[c for c in cols if c in df.columns]]

            if start_date:
                df = df[df["trade_date"] >= start_date]
            if end_date:
                df = df[df["trade_date"] <= end_date]

            return df

        except Exception as e:
            logger.error(f"新浪采集 {ts_code} K线失败: {e}")
            return pd.DataFrame()
"""
同花顺金融数据API采集器
使用 fuyao.aicubes.cn REST API 获取 A 股实时行情数据
"""
import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Optional, Dict
from app.utils.logger import logger
from app.config import settings


class THSCollector:
    """同花顺金融数据采集器"""

    BASE_URL = "https://fuyao.aicubes.cn"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ths_api_key
        if not self.api_key:
            raise ValueError("THS_API_KEY 未配置，请在 .env 中设置")
        self.session = requests.Session()
        self.session.headers.update({
            "X-api-key": self.api_key,
            "Content-Type": "application/json",
        })

    def _request(self, method: str, path: str, params: dict = None, json_data: dict = None, retries: int = 3) -> dict:
        """发送API请求，带重试"""
        url = f"{self.BASE_URL}{path}"
        for attempt in range(retries):
            try:
                if method == "GET":
                    r = self.session.get(url, params=params, timeout=30)
                else:
                    r = self.session.post(url, params=params, json=json_data, timeout=30)

                if r.status_code == 429:
                    wait = min(2 ** attempt, 30)
                    logger.warning(f"API限流，等待 {wait}s 后重试...")
                    time.sleep(wait)
                    continue

                data = r.json()
                if data.get("code") not in (0, 0):
                    logger.error(f"API错误: {path} - {data.get('message')}")
                    return data

                return data

            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 {path}，第 {attempt+1} 次重试...")
                time.sleep(2)
            except Exception as e:
                logger.error(f"请求异常 {path}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    return {"code": -1, "message": str(e), "data": None}

    def get_snapshot(self, security_codes: List[str] = None) -> pd.DataFrame:
        """
        获取全市场A股实时行情快照（一次返回全部5000+只股票）
        返回: DataFrame with columns: ts_code, ticker, volume, turnover, last_price,
              price_change, price_change_ratio_pct, open_price, high_price, low_price, prev_price
        """
        try:
            params = {}
            if security_codes:
                params["thscode"] = ",".join(security_codes)

            data = self._request("GET", "/api/a-share/prices/snapshot", params=params)
            if data.get("code") != 0 or not data.get("data"):
                logger.error(f"快照数据获取失败: {data.get('message')}")
                return pd.DataFrame()

            items = data["data"].get("item", [])
            if not items:
                logger.warning("快照数据为空")
                return pd.DataFrame()

            total = data["data"].get("total", len(items))
            logger.info(f"获取到 {len(items)} 只股票行情数据 (total={total})")

            df = pd.DataFrame(items)
            df.rename(columns={
                "thscode": "ts_code",
                "last_price": "close",
                "open_price": "open",
                "high_price": "high",
                "low_price": "low",
                "prev_price": "pre_close",
                "price_change": "change",
                "price_change_ratio_pct": "pct_chg",
                "volume": "vol",
                "turnover": "amount",
            }, inplace=True)

            df["trade_date"] = datetime.now().strftime("%Y%m%d")
            df["amount"] = df["amount"] / 1000  # 元转千元
            df["source"] = "ths"
            df["turn"] = 0.0

            logger.info(f"同花顺快照: {len(df)} 只股票")
            return df

        except Exception as e:
            logger.error(f"获取快照失败: {e}")
            return pd.DataFrame()

    def get_historical_kline(
        self,
        ts_code: str,
        interval: str = "1d",
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        获取历史K线数据（需要先触发全市场数据导出）
        ts_code: 600000.SH
        interval: 1d(日线), 1wk(周线), 1mo(月线)
        """
        try:
            if not start_date:
                start_date = (datetime.now() - pd.Timedelta(days=365)).strftime("%Y%m%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")

            params = {
                "thscode": ts_code,
                "interval": interval,
                "start": start_date,
                "end": end_date,
            }

            data = self._request("GET", "/api/a-share/prices/historical", params=params)
            if data.get("code") != 0:
                logger.warning(f"历史K线 {ts_code}: {data.get('message')}")
                return pd.DataFrame()

            items = data.get("data", {}).get("item", [])
            if not items:
                return pd.DataFrame()

            df = pd.DataFrame(items)
            df["ts_code"] = ts_code

            if "trade_date" in df.columns:
                df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y%m%d")

            col_map = {
                "open": "open", "high": "high", "low": "low", "close": "close",
                "volume": "vol", "amount": "amount", "pct_chg": "pct_chg",
            }
            df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

            for col in ["open", "high", "low", "close", "vol", "amount"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            if "amount" in df.columns:
                df["amount"] = df["amount"] / 1000

            if "pre_close" not in df.columns and "close" in df.columns:
                df["pre_close"] = df["close"].shift(1)
                df["pre_close"] = df["pre_close"].fillna(df["open"] if "open" in df.columns else df["close"])

            if "change" not in df.columns and "close" in df.columns and "pre_close" in df.columns:
                df["change"] = df["close"] - df["pre_close"]

            if "pct_chg" not in df.columns and "close" in df.columns and "pre_close" in df.columns:
                df["pct_chg"] = ((df["close"] - df["pre_close"]) / df["pre_close"].replace(0, None) * 100).round(3)

            df["source"] = "ths"
            df["turn"] = 0.0

            logger.info(f"历史K线 {ts_code}: {len(df)} 条")
            return df

        except Exception as e:
            logger.error(f"获取历史K线 {ts_code} 失败: {e}")
            return pd.DataFrame()

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表（从快照接口提取）
        返回: DataFrame with ts_code, ticker, name
        """
        try:
            df = self.get_snapshot()
            if df.empty:
                return pd.DataFrame()

            stock_list = df[["ts_code", "ticker"]].copy()
            stock_list = stock_list.drop_duplicates(subset=["ts_code"])
            logger.info(f"股票列表: {len(stock_list)} 只")
            return stock_list

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def save_snapshot_to_db(self, db_session, df: pd.DataFrame = None) -> int:
        """
        保存快照数据到 ods_stock_daily 表（批量 upsert）
        返回: 插入行数
        """
        if df is None:
            df = self.get_snapshot()

        if df.empty:
            return 0

        import numpy as np
        from sqlalchemy import text

        df = df.replace({np.nan: None})

        today = datetime.now().strftime("%Y%m%d")
        batch_size = 200
        total = 0
        rows = df.to_dict("records")

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            values_parts = []
            params = {}

            for j, row in enumerate(batch):
                idx = i + j
                values_parts.append(
                    f"(:ts_{idx}, :td_{idx}, :open_{idx}, :high_{idx}, :low_{idx}, "
                    f":close_{idx}, :pre_{idx}, :chg_{idx}, :pct_{idx}, :vol_{idx}, "
                    f":amt_{idx}, :turn_{idx}, :src_{idx})"
                )
                params.update({
                    f"ts_{idx}": row["ts_code"],
                    f"td_{idx}": today,
                    f"open_{idx}": row.get("open"),
                    f"high_{idx}": row.get("high"),
                    f"low_{idx}": row.get("low"),
                    f"close_{idx}": row.get("close"),
                    f"pre_{idx}": row.get("pre_close"),
                    f"chg_{idx}": row.get("change"),
                    f"pct_{idx}": row.get("pct_chg"),
                    f"vol_{idx}": row.get("vol"),
                    f"amt_{idx}": row.get("amount"),
                    f"turn_{idx}": row.get("turn", 0),
                    f"src_{idx}": "ths",
                })

            sql = text(
                "INSERT INTO ods_stock_daily "
                "(ts_code, trade_date, `open`, high, low, `close`, pre_close, "
                "`change`, pct_chg, vol, amount, turn, source) "
                "VALUES " + ", ".join(values_parts) + " "
                "ON DUPLICATE KEY UPDATE "
                "`open` = VALUES(`open`), high = VALUES(high), low = VALUES(low), "
                "`close` = VALUES(`close`), pre_close = VALUES(pre_close), "
                "`change` = VALUES(`change`), pct_chg = VALUES(pct_chg), "
                "vol = VALUES(vol), amount = VALUES(amount), turn = VALUES(turn), "
                "source = VALUES(source)"
            )

            db_session.execute(sql, params)
            db_session.commit()
            total += len(batch)
            logger.info(f"已保存 {total}/{len(rows)} 条")

        logger.info(f"快照数据保存完成: {total} 条")
        return total


# 测试入口
if __name__ == "__main__":
    collector = THSCollector()
    df = collector.get_snapshot()
    print(f"获取到 {len(df)} 只股票")
    print(df.head())
    print(df.columns.tolist())
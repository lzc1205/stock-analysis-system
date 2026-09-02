"""
数据清洗模块
处理从数据源采集的原始数据，进行去重、空值处理、格式统一
"""
import pandas as pd
import numpy as np
from datetime import datetime
from app.utils.logger import logger


class DataCleaner:
    def clean_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗日线行情数据"""
        if df.empty:
            return df

        df = df.copy()

        numeric_cols = ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount", "turn"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")

        # 如果缺少 change 列，根据 close 和 pre_close 计算
        if "change" not in df.columns and "close" in df.columns and "pre_close" in df.columns:
            df["change"] = df["close"] - df["pre_close"]

        # 去除重复行
        if "ts_code" in df.columns and "trade_date" in df.columns:
            df = df.drop_duplicates(subset=["ts_code", "trade_date"], keep="last")

        # 填充空值（只处理存在的列）
        existing_numeric = [c for c in numeric_cols if c in df.columns]
        df[existing_numeric] = df[existing_numeric].fillna(0)

        # 计算振幅
        if "high" in df.columns and "low" in df.columns and "pre_close" in df.columns:
            df["amplitude"] = np.where(
                df["pre_close"] > 0,
                ((df["high"] - df["low"]) / df["pre_close"] * 100).round(3),
                0,
            )

        # 过滤异常数据
        if "pct_chg" in df.columns:
            df = df[(df["pct_chg"] >= -20) & (df["pct_chg"] <= 20)]

        if "close" in df.columns:
            df = df[df["close"] > 0]

        logger.info(f"日线数据清洗完成，清洗后 {len(df)} 条")
        return df

    def clean_financial_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗财务报表数据"""
        if df.empty:
            return df

        df = df.copy()

        # 日期列转换
        date_cols = ["ann_date", "f_ann_date", "end_date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # 数值列转换
        numeric_cols = [
            "revenue", "total_cogs", "operate_profit", "total_profit",
            "n_income", "eps", "total_assets", "total_liab", "total_hldr_eqy",
            "n_cashflow_act", "n_cashflow_inv", "n_cashflow_fin",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 去除重复
        if "ts_code" in df.columns and "end_date" in df.columns and "report_type" in df.columns:
            df = df.drop_duplicates(subset=["ts_code", "end_date", "report_type"], keep="last")

        # 填充空值
        df[numeric_cols] = df[numeric_cols].fillna(0)

        logger.info(f"财务数据清洗完成，清洗后 {len(df)} 条")
        return df

    def clean_money_flow_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗资金流向数据"""
        if df.empty:
            return df

        df = df.copy()

        numeric_cols = [
            "buy_sm_vol", "sell_sm_vol", "buy_md_vol", "sell_md_vol",
            "buy_lg_vol", "sell_lg_vol", "buy_elg_vol", "sell_elg_vol",
            "net_mf_vol",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")

        if "ts_code" in df.columns and "trade_date" in df.columns:
            df = df.drop_duplicates(subset=["ts_code", "trade_date"], keep="last")

        df[numeric_cols] = df[numeric_cols].fillna(0)

        logger.info(f"资金流向数据清洗完成，清洗后 {len(df)} 条")
        return df
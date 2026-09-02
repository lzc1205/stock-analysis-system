"""
技术指标计算模块
使用 TA-Lib 计算 MA/MACD/RSI/KDJ 等技术指标
如果 TA-Lib 安装失败，回退到纯 Python 实现
"""
import numpy as np
import pandas as pd
from app.utils.logger import logger

# 尝试导入 TA-Lib
try:
    import talib
    HAS_TALIB = True
    logger.info("TA-Lib 加载成功，使用原生 C 库计算技术指标")
except ImportError:
    HAS_TALIB = False
    logger.warning("TA-Lib 未安装，使用纯 Python 实现技术指标计算")


def calculate_ma(close: np.ndarray, periods: list = [5, 10, 20, 60]) -> dict:
    """
    计算移动平均线 MA
    :param close: 收盘价序列
    :param periods: 周期列表
    :return: {ma5: [...], ma10: [...], ...}
    """
    result = {}
    for period in periods:
        if HAS_TALIB:
            ma = talib.MA(close, timeperiod=period)
        else:
            ma = pd.Series(close).rolling(window=period).mean().values
        result[f"ma{period}"] = np.where(np.isnan(ma), 0, ma).round(3)
    return result


def calculate_macd(
    close: np.ndarray,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict:
    """
    计算 MACD 指标
    :param close: 收盘价序列
    :return: {dif: [...], dea: [...], macd_bar: [...]}
    """
    if HAS_TALIB:
        dif, dea, macd_bar = talib.MACD(
            close, fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
    else:
        # 纯 Python 实现
        ema_fast = pd.Series(close).ewm(span=fast, adjust=False).mean()
        ema_slow = pd.Series(close).ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd_bar = 2 * (dif - dea)
        dif, dea, macd_bar = dif.values, dea.values, macd_bar.values

    return {
        "dif": np.where(np.isnan(dif), 0, dif).round(3),
        "dea": np.where(np.isnan(dea), 0, dea).round(3),
        "macd_bar": np.where(np.isnan(macd_bar), 0, macd_bar).round(3),
    }


def calculate_rsi(close: np.ndarray, periods: list = [6, 12, 24]) -> dict:
    """
    计算 RSI 指标
    :param close: 收盘价序列
    :param periods: 周期列表
    :return: {rsi6: [...], rsi12: [...], rsi24: [...]}
    """
    result = {}
    for period in periods:
        if HAS_TALIB:
            rsi = talib.RSI(close, timeperiod=period)
        else:
            delta = pd.Series(close).diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi = rsi.values
        result[f"rsi{period}"] = np.where(np.isnan(rsi), 50, rsi).round(3)
    return result


def calculate_kdj(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 9,
    k_period: int = 3,
    d_period: int = 3,
) -> dict:
    """
    计算 KDJ 指标
    :return: {k: [...], d: [...], j: [...]}
    """
    if HAS_TALIB:
        k, d = talib.STOCH(
            high, low, close,
            fastk_period=period,
            slowk_period=k_period,
            slowk_matype=0,
            slowd_period=d_period,
            slowd_matype=0,
        )
        j = 3 * k - 2 * d
    else:
        # 纯 Python 实现
        low_min = pd.Series(low).rolling(window=period).min()
        high_max = pd.Series(high).rolling(window=period).max()
        rsv = (pd.Series(close) - low_min) / (high_max - low_min).replace(0, np.nan) * 100

        k = rsv.ewm(com=k_period - 1, adjust=False).mean()
        d = k.ewm(com=d_period - 1, adjust=False).mean()
        j = 3 * k - 2 * d
        k, d, j = k.values, d.values, j.values

    return {
        "k": np.where(np.isnan(k), 50, k).round(3),
        "d": np.where(np.isnan(d), 50, d).round(3),
        "j": np.where(np.isnan(j), 50, j).round(3),
    }


def calculate_bollinger(
    close: np.ndarray,
    period: int = 20,
    nbdev: int = 2,
) -> dict:
    """
    计算布林带
    :return: {upper: [...], middle: [...], lower: [...]}
    """
    if HAS_TALIB:
        upper, middle, lower = talib.BBANDS(
            close, timeperiod=period, nbdevup=nbdev, nbdevdn=nbdev, matype=0
        )
    else:
        middle = pd.Series(close).rolling(window=period).mean()
        std = pd.Series(close).rolling(window=period).std()
        upper = middle + nbdev * std
        lower = middle - nbdev * std
        middle, upper, lower = middle.values, upper.values, lower.values

    return {
        "upper": np.where(np.isnan(upper), 0, upper).round(3),
        "middle": np.where(np.isnan(middle), 0, middle).round(3),
        "lower": np.where(np.isnan(lower), 0, lower).round(3),
    }


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有技术指标并添加到 DataFrame
    :param df: 包含 open/high/low/close/vol 列的 DataFrame
    :return: 添加了技术指标列的 DataFrame
    """
    if df.empty:
        return df

    df = df.copy()
    close = df["close"].values.astype(np.float64)
    high = df["high"].values.astype(np.float64)
    low = df["low"].values.astype(np.float64)

    # MA
    ma_result = calculate_ma(close)
    for key, values in ma_result.items():
        df[key] = values

    # MACD
    macd_result = calculate_macd(close)
    for key, values in macd_result.items():
        df[key] = values

    # RSI
    rsi_result = calculate_rsi(close)
    for key, values in rsi_result.items():
        df[key] = values

    # KDJ
    kdj_result = calculate_kdj(high, low, close)
    for key, values in kdj_result.items():
        df[key] = values

    logger.info(f"技术指标计算完成，共处理 {len(df)} 条数据")
    return df
"""
技术指标服务
"""
from sqlalchemy.orm import Session
from app.models.dws import DwsStockDailyWide
from app.models.ads import AdsTechnicalRadar
from app.utils.logger import logger


class IndicatorService:
    def __init__(self, db: Session):
        self.db = db

    def get_daily_indicators(self, ts_code: str, days: int = 60) -> list:
        """获取每日技术指标"""
        indicators = (
            self.db.query(DwsStockDailyWide)
            .filter(DwsStockDailyWide.ts_code == ts_code)
            .order_by(DwsStockDailyWide.trade_date.desc())
            .limit(days)
            .all()
        )
        return [
            {
                "ts_code": i.ts_code,
                "trade_date": str(i.trade_date),
                "close": float(i.close) if i.close else None,
                "pct_chg": float(i.pct_chg) if i.pct_chg else None,
                "ma5": float(i.ma5) if i.ma5 else None,
                "ma10": float(i.ma10) if i.ma10 else None,
                "ma20": float(i.ma20) if i.ma20 else None,
                "ma60": float(i.ma60) if i.ma60 else None,
                "dif": float(i.dif) if i.dif else None,
                "dea": float(i.dea) if i.dea else None,
                "macd_bar": float(i.macd_bar) if i.macd_bar else None,
                "rsi6": float(i.rsi6) if i.rsi6 else None,
                "rsi12": float(i.rsi12) if i.rsi12 else None,
                "rsi24": float(i.rsi24) if i.rsi24 else None,
                "k": float(i.k) if i.k else None,
                "d": float(i.d) if i.d else None,
                "j": float(i.j) if i.j else None,
            }
            for i in reversed(indicators)
        ]

    def get_latest_signal(self, ts_code: str) -> dict | None:
        """获取最新交易信号"""
        radar = (
            self.db.query(AdsTechnicalRadar)
            .filter(AdsTechnicalRadar.ts_code == ts_code)
            .order_by(AdsTechnicalRadar.trade_date.desc())
            .first()
        )
        if not radar:
            return None
        return {
            "ts_code": radar.ts_code,
            "trade_date": str(radar.trade_date),
            "trend_score": float(radar.trend_score) if radar.trend_score else None,
            "momentum_score": float(radar.momentum_score) if radar.momentum_score else None,
            "volatility_score": float(radar.volatility_score) if radar.volatility_score else None,
            "volume_score": float(radar.volume_score) if radar.volume_score else None,
            "overall_score": float(radar.overall_score) if radar.overall_score else None,
            "signal": radar.signal,
        }
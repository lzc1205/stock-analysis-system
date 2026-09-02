"""
股票数据服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.dwd import DwdStockInfo
from app.models.ads import AdsStockOverview, AdsKlineData, AdsTechnicalRadar, AdsCapitalFlow, AdsFinancialHealth
from app.models.dws import DwsIndustryDaily
from app.utils.logger import logger


class StockService:
    def __init__(self, db: Session):
        self.db = db

    def get_stock_list(self, keyword: str = None) -> list:
        """获取股票列表"""
        query = self.db.query(AdsStockOverview)
        if keyword:
            query = query.filter(
                (AdsStockOverview.name.like(f"%{keyword}%"))
                | (AdsStockOverview.ts_code.like(f"%{keyword}%"))
            )
        stocks = query.order_by(AdsStockOverview.latest_amount.desc()).all()
        return [
            {
                "ts_code": s.ts_code,
                "name": s.name,
                "industry": s.industry,
                "latest_price": float(s.latest_price) if s.latest_price else None,
                "latest_pct_chg": float(s.latest_pct_chg) if s.latest_pct_chg else None,
            }
            for s in stocks
        ]

    def get_stock_overview(self, ts_code: str) -> dict | None:
        """获取个股概览"""
        stock = self.db.query(AdsStockOverview).filter(AdsStockOverview.ts_code == ts_code).first()
        if not stock:
            return None
        return {
            "ts_code": stock.ts_code,
            "name": stock.name,
            "industry": stock.industry,
            "latest_price": float(stock.latest_price or 0),
            "latest_pct_chg": float(stock.latest_pct_chg or 0),
            "latest_vol": float(stock.latest_vol or 0),
            "latest_amount": float(stock.latest_amount or 0),
            "pe": float(stock.pe or 0),
            "pb": float(stock.pb or 0),
            "total_mv": float(stock.total_mv or 0),
            "circ_mv": float(stock.circ_mv or 0),
            "ma5": float(stock.ma5 or 0),
            "ma20": float(stock.ma20 or 0),
            "dif": float(stock.dif or 0),
            "dea": float(stock.dea or 0),
            "rsi6": float(stock.rsi6 or 50),
            "net_mf_vol": float(stock.net_mf_vol or 0),
            "update_date": str(stock.update_date) if stock.update_date else None,
        }

    def get_kline_data(self, ts_code: str, days: int = 120) -> list:
        """获取K线数据"""
        klines = (
            self.db.query(AdsKlineData)
            .filter(AdsKlineData.ts_code == ts_code)
            .order_by(AdsKlineData.trade_date.desc())
            .limit(days)
            .all()
        )
        return [
            {
                "ts_code": k.ts_code,
                "trade_date": str(k.trade_date),
                "open": float(k.open) if k.open else None,
                "high": float(k.high) if k.high else None,
                "low": float(k.low) if k.low else None,
                "close": float(k.close) if k.close else None,
                "vol": float(k.vol) if k.vol else None,
                "amount": float(k.amount) if k.amount else None,
                "pct_chg": float(k.pct_chg) if k.pct_chg else None,
                "ma5": float(k.ma5) if k.ma5 else None,
                "ma10": float(k.ma10) if k.ma10 else None,
                "ma20": float(k.ma20) if k.ma20 else None,
                "ma60": float(k.ma60) if k.ma60 else None,
            }
            for k in reversed(klines)
        ]

    def get_technical_radar(self, ts_code: str) -> dict | None:
        """获取技术指标雷达数据"""
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

    def get_capital_flow(self, ts_code: str, days: int = 30) -> list:
        """获取资金流向数据"""
        flows = (
            self.db.query(AdsCapitalFlow)
            .filter(AdsCapitalFlow.ts_code == ts_code)
            .order_by(AdsCapitalFlow.trade_date.desc())
            .limit(days)
            .all()
        )
        return [
            {
                "ts_code": f.ts_code,
                "trade_date": str(f.trade_date),
                "net_sm": float(f.net_sm) if f.net_sm else None,
                "net_md": float(f.net_md) if f.net_md else None,
                "net_lg": float(f.net_lg) if f.net_lg else None,
                "net_elg": float(f.net_elg) if f.net_elg else None,
                "net_total": float(f.net_total) if f.net_total else None,
            }
            for f in reversed(flows)
        ]

    def get_financial_health(self, ts_code: str) -> dict | None:
        """获取财务健康度数据"""
        financial = (
            self.db.query(AdsFinancialHealth)
            .filter(AdsFinancialHealth.ts_code == ts_code)
            .order_by(AdsFinancialHealth.end_date.desc())
            .first()
        )
        if not financial:
            return None
        return {
            "ts_code": financial.ts_code,
            "end_date": str(financial.end_date),
            "roe": float(financial.roe or 0),
            "gross_margin": float(financial.gross_margin or 0),
            "net_margin": float(financial.net_margin or 0),
            "debt_ratio": float(financial.debt_ratio or 0),
            "revenue_yoy": float(financial.revenue_yoy or 0),
            "n_income_yoy": float(financial.n_income_yoy or 0),
            "eps": float(financial.eps or 0),
            "health_score": float(financial.health_score or 0),
            "health_level": financial.health_level,
        }

    def get_industry_compare(self) -> list:
        """获取行业对比数据（最新交易日）"""
        # 获取最新交易日
        latest_date_query = (
            self.db.query(func.max(DwsIndustryDaily.trade_date))
            .scalar_subquery()
        )
        rows = (
            self.db.query(DwsIndustryDaily)
            .filter(DwsIndustryDaily.trade_date == latest_date_query)
            .order_by(DwsIndustryDaily.avg_pct_chg.desc())
            .limit(15)
            .all()
        )
        return [
            {
                "industry_l1": r.industry_l1,
                "trade_date": str(r.trade_date),
                "stock_count": r.stock_count,
                "rise_count": r.rise_count,
                "fall_count": r.fall_count,
                "avg_pct_chg": float(r.avg_pct_chg) if r.avg_pct_chg else None,
                "total_amount": float(r.total_amount) if r.total_amount else None,
            }
            for r in rows
        ]

    def get_market_analysis(self) -> dict:
        """获取全市场统计分析"""
        stocks = self.db.query(AdsStockOverview).filter(
            AdsStockOverview.latest_pct_chg.isnot(None)
        ).all()

        if not stocks:
            return {}

        df = [
            {
                "ts_code": s.ts_code,
                "name": s.name,
                "industry": s.industry,
                "pct_chg": float(s.latest_pct_chg or 0),
                "price": float(s.latest_price or 0),
                "amount": float(s.latest_amount or 0),
                "pe": float(s.pe) if s.pe and s.pe > 0 else None,
                "pb": float(s.pb) if s.pb and s.pb > 0 else None,
                "total_mv": float(s.total_mv or 0),
                "net_mf_vol": float(s.net_mf_vol or 0),
            }
            for s in stocks
        ]

        pct_list = [d["pct_chg"] for d in df]
        amount_list = [d["amount"] for d in df if d["amount"] > 0]
        pe_list = [d["pe"] for d in df if d["pe"]]
        mv_list = [d["total_mv"] for d in df if d["total_mv"] > 0]

        # 涨跌幅分布
        bins = {
            "limit_up": sum(1 for v in pct_list if v >= 9.9),
            "gt7": sum(1 for v in pct_list if 7 <= v < 9.9),
            "gt5": sum(1 for v in pct_list if 5 <= v < 7),
            "gt3": sum(1 for v in pct_list if 3 <= v < 5),
            "gt1": sum(1 for v in pct_list if 1 <= v < 3),
            "gt0": sum(1 for v in pct_list if 0 < v < 1),
            "eq0": sum(1 for v in pct_list if v == 0),
            "lt0": sum(1 for v in pct_list if -1 < v < 0),
            "lt_1": sum(1 for v in pct_list if -3 <= v <= -1),
            "lt_3": sum(1 for v in pct_list if -5 <= v < -3),
            "lt_5": sum(1 for v in pct_list if -7 <= v < -5),
            "lt_7": sum(1 for v in pct_list if -9.9 < v < -7),
            "limit_down": sum(1 for v in pct_list if v <= -9.9),
        }

        up_count = sum(1 for v in pct_list if v > 0)
        down_count = sum(1 for v in pct_list if v < 0)
        flat_count = sum(1 for v in pct_list if v == 0)

        # 行业涨幅榜
        industry_map = {}
        for d in df:
            ind = d["industry"] or "未知"
            if ind not in industry_map:
                industry_map[ind] = {"pct_list": [], "count": 0}
            industry_map[ind]["pct_list"].append(d["pct_chg"])
            industry_map[ind]["count"] += 1

        industry_rank = []
        for ind, v in industry_map.items():
            if v["count"] >= 3:
                industry_rank.append({
                    "name": ind,
                    "count": v["count"],
                    "avg_pct": round(sum(v["pct_list"]) / len(v["pct_list"]), 2),
                    "up_ratio": round(sum(1 for p in v["pct_list"] if p > 0) / len(v["pct_list"]) * 100, 1),
                })
        industry_rank.sort(key=lambda x: x["avg_pct"], reverse=True)

        # 资金流向 TOP10
        top_money = sorted(df, key=lambda x: x["net_mf_vol"], reverse=True)[:10]
        top_money_list = [
            {"name": d["name"], "ts_code": d["ts_code"], "net_mf_vol": d["net_mf_vol"]}
            for d in top_money
        ]

        return {
            "total_stocks": len(df),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "up_ratio": round(up_count / len(df) * 100, 1),
            "avg_pct": round(sum(pct_list) / len(pct_list), 2),
            "avg_amount": round(sum(amount_list) / len(amount_list), 2) if amount_list else 0,
            "avg_pe": round(sum(pe_list) / len(pe_list), 2) if pe_list else None,
            "pct_distribution": bins,
            "industry_rank": industry_rank[:10],
            "top_money_flow": top_money_list,
        }
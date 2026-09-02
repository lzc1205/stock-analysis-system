"""
大屏数据服务
聚合多维度数据供大屏展示
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from app.services.stock_service import StockService
from app.utils.database import SessionLocal
from app.utils.logger import logger


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)

    def get_dashboard_data(self, ts_code: str) -> dict:
        """获取大屏所需的全部数据（并行查询，大幅提升切换速度）"""
        results = {}

        def _query(method_name, *args):
            db = SessionLocal()
            try:
                svc = StockService(db)
                method = getattr(svc, method_name)
                return method_name, method(*args)
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_query, "get_stock_overview", ts_code): "stock_overview",
                executor.submit(_query, "get_kline_data", ts_code, 120): "kline_data",
                executor.submit(_query, "get_technical_radar", ts_code): "technical_radar",
                executor.submit(_query, "get_capital_flow", ts_code, 30): "capital_flow",
                executor.submit(_query, "get_financial_health", ts_code): "financial_health",
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    _, data = future.result()
                    results[key] = data
                except Exception as e:
                    logger.error(f"查询 {key} 失败: {e}")
                    results[key] = None

        return {
            "stock_overview": results.get("stock_overview"),
            "kline_data": results.get("kline_data") or [],
            "technical_radar": results.get("technical_radar"),
            "capital_flow": results.get("capital_flow") or [],
            "financial_health": results.get("financial_health"),
        }
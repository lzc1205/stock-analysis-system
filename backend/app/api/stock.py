"""
股票相关API接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.schemas import APIResponse
from app.services.stock_service import StockService

router = APIRouter(prefix="/api/stock", tags=["股票数据"])


@router.get("/list", response_model=APIResponse)
def get_stock_list(
    keyword: str = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """获取股票列表"""
    service = StockService(db)
    stocks = service.get_stock_list(keyword)
    return APIResponse(data=stocks)


@router.get("/overview/{ts_code}", response_model=APIResponse)
def get_stock_overview(
    ts_code: str,
    db: Session = Depends(get_db),
):
    """获取个股概览"""
    service = StockService(db)
    overview = service.get_stock_overview(ts_code)
    return APIResponse(data=overview)


@router.get("/kline/{ts_code}", response_model=APIResponse)
def get_kline_data(
    ts_code: str,
    days: int = Query(120, ge=1, le=500, description="获取天数"),
    db: Session = Depends(get_db),
):
    """获取K线数据"""
    service = StockService(db)
    kline = service.get_kline_data(ts_code, days)
    return APIResponse(data=kline)


@router.get("/technical/{ts_code}", response_model=APIResponse)
def get_technical_radar(
    ts_code: str,
    db: Session = Depends(get_db),
):
    """获取技术指标雷达数据"""
    service = StockService(db)
    radar = service.get_technical_radar(ts_code)
    return APIResponse(data=radar)


@router.get("/capital_flow/{ts_code}", response_model=APIResponse)
def get_capital_flow(
    ts_code: str,
    days: int = Query(30, ge=1, le=365, description="获取天数"),
    db: Session = Depends(get_db),
):
    """获取资金流向数据"""
    service = StockService(db)
    flow = service.get_capital_flow(ts_code, days)
    return APIResponse(data=flow)


@router.get("/financial/{ts_code}", response_model=APIResponse)
def get_financial_health(
    ts_code: str,
    db: Session = Depends(get_db),
):
    """获取财务健康度数据"""
    service = StockService(db)
    financial = service.get_financial_health(ts_code)
    return APIResponse(data=financial)


@router.get("/industry_compare", response_model=APIResponse)
def get_industry_compare(
    db: Session = Depends(get_db),
):
    """获取行业对比数据"""
    service = StockService(db)
    data = service.get_industry_compare()
    return APIResponse(data=data)


@router.get("/market_analysis", response_model=APIResponse)
def get_market_analysis(
    db: Session = Depends(get_db),
):
    """获取全市场统计分析"""
    service = StockService(db)
    data = service.get_market_analysis()
    return APIResponse(data=data)
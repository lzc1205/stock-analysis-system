"""
技术指标相关API接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.schemas import APIResponse
from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/api/indicator", tags=["技术指标"])


@router.get("/daily/{ts_code}", response_model=APIResponse)
def get_daily_indicators(
    ts_code: str,
    days: int = Query(60, ge=1, le=365, description="获取天数"),
    db: Session = Depends(get_db),
):
    """获取个股技术指标数据"""
    service = IndicatorService(db)
    indicators = service.get_daily_indicators(ts_code, days)
    return APIResponse(data=indicators)


@router.get("/signal/{ts_code}", response_model=APIResponse)
def get_signal(
    ts_code: str,
    db: Session = Depends(get_db),
):
    """获取最新交易信号"""
    service = IndicatorService(db)
    signal = service.get_latest_signal(ts_code)
    return APIResponse(data=signal)
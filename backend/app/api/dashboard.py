"""
大屏数据聚合接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.schemas import APIResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["大屏数据"])


@router.get("/data/{ts_code}", response_model=APIResponse)
def get_dashboard_data(
    ts_code: str,
    db: Session = Depends(get_db),
):
    """获取大屏所需的全部数据"""
    service = DashboardService(db)
    data = service.get_dashboard_data(ts_code)
    return APIResponse(data=data)
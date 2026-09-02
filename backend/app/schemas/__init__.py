from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime


class StockOverviewResponse(BaseModel):
    ts_code: str
    name: Optional[str] = None
    industry: Optional[str] = None
    latest_price: Optional[float] = None
    latest_pct_chg: Optional[float] = None
    latest_vol: Optional[float] = None
    latest_amount: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    total_mv: Optional[float] = None
    circ_mv: Optional[float] = None
    update_date: Optional[date] = None

    class Config:
        from_attributes = True


class KlineDataResponse(BaseModel):
    ts_code: str
    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    vol: Optional[float] = None
    amount: Optional[float] = None
    pct_chg: Optional[float] = None
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None

    class Config:
        from_attributes = True


class TechnicalRadarResponse(BaseModel):
    ts_code: str
    trade_date: date
    trend_score: Optional[float] = None
    momentum_score: Optional[float] = None
    volatility_score: Optional[float] = None
    volume_score: Optional[float] = None
    overall_score: Optional[float] = None
    signal: Optional[str] = None

    class Config:
        from_attributes = True


class CapitalFlowResponse(BaseModel):
    ts_code: str
    trade_date: date
    net_sm: Optional[float] = None
    net_md: Optional[float] = None
    net_lg: Optional[float] = None
    net_elg: Optional[float] = None
    net_total: Optional[float] = None

    class Config:
        from_attributes = True


class FinancialHealthResponse(BaseModel):
    ts_code: str
    end_date: date
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_ratio: Optional[float] = None
    revenue_yoy: Optional[float] = None
    n_income_yoy: Optional[float] = None
    eps: Optional[float] = None
    health_score: Optional[float] = None
    health_level: Optional[str] = None

    class Config:
        from_attributes = True


class AIChatRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    question: str = Field(..., description="用户问题")
    stock_code: Optional[str] = Field(None, description="当前选中的股票代码")


class AIChatResponse(BaseModel):
    answer: str = Field(..., description="AI回答")
    sql_used: Optional[str] = Field(None, description="使用的SQL")
    data: List[Any] = Field(default_factory=list, description="查询到的原始数据")
    intent: str = Field(..., description="意图类型")
    disclaimer: str = Field(default="以上内容由AI生成，仅供参考，不构成投资建议", description="免责声明")


class DashboardDataResponse(BaseModel):
    stock_overview: Optional[StockOverviewResponse] = None
    kline_data: List[KlineDataResponse] = Field(default_factory=list)
    technical_radar: Optional[TechnicalRadarResponse] = None
    capital_flow: Optional[CapitalFlowResponse] = None
    financial_health: Optional[FinancialHealthResponse] = None


class StockListResponse(BaseModel):
    ts_code: str
    name: Optional[str] = None
    industry: Optional[str] = None

    class Config:
        from_attributes = True


class APIResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None
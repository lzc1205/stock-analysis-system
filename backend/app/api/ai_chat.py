"""
AI 智能问答接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.schemas import APIResponse, AIChatRequest
from app.services.ai_chat_service import AIChatService

router = APIRouter(prefix="/api/ai", tags=["AI智能问答"])


@router.post("/chat", response_model=APIResponse)
def ai_chat(
    request: AIChatRequest,
    db: Session = Depends(get_db),
):
    """AI智能问答"""
    service = AIChatService(db)
    result = service.chat(
        session_id=request.session_id,
        question=request.question,
        stock_code=request.stock_code,
    )
    return APIResponse(data=result)


@router.get("/history/{session_id}", response_model=APIResponse)
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """获取对话历史"""
    service = AIChatService(db)
    history = service.get_chat_history(session_id)
    return APIResponse(data=history)


@router.delete("/history/{session_id}", response_model=APIResponse)
def clear_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """清除对话历史"""
    service = AIChatService(db)
    service.clear_chat_history(session_id)
    return APIResponse(message="对话历史已清除")
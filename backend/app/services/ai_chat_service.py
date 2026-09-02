"""
AI 智能问答服务
"""
import json
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.logger import logger
from app.utils.cache import cache_get, cache_set, cache_delete
from ai.intent_recognition import recognize_intent
from ai.text_to_sql import generate_sql
from ai.answer_generator import generate_answer
from ai.prompt_templates import DISCLAIMER_TEXT

MAX_HISTORY_ROUNDS = 20
MAX_QUESTIONS_PER_MINUTE = 10


class AIChatService:
    def __init__(self, db: Session):
        self.db = db

    def chat(self, session_id: str, question: str, stock_code: str = None) -> dict:
        """处理用户提问"""
        # 限流检查
        rate_key = f"chat_rate:{session_id}"
        count = cache_get(rate_key)
        if count and int(count) >= MAX_QUESTIONS_PER_MINUTE:
            return {
                "answer": "提问过于频繁，请稍后再试。",
                "sql_used": None,
                "data": [],
                "intent": "系统",
                "disclaimer": DISCLAIMER_TEXT,
            }

        # 更新限流计数
        cache_set(rate_key, str(int(count or 0) + 1), expire=60)

        # 意图识别
        intent_result = recognize_intent(question)
        intent = intent_result.get("intent", "闲聊")
        logger.info(f"意图识别: {intent}")

        # 如果是闲聊，直接返回
        if intent == "闲聊":
            return {
                "answer": "您好！我是金融数据分析助手。我可以帮您查询股票行情、分析技术指标、解读财务数据。请问您想了解哪只股票？",
                "sql_used": None,
                "data": [],
                "intent": intent,
                "disclaimer": DISCLAIMER_TEXT,
            }

        # 如果是投资建议，给谨慎回答
        if intent == "投资建议":
            return {
                "answer": "我理解您想了解投资建议。不过需要提醒您，我无法提供投资建议，但我可以为您分析该股票的技术面、基本面和资金面数据，供您参考。\n\n您想了解哪方面的数据？\n\n" + DISCLAIMER_TEXT,
                "sql_used": None,
                "data": [],
                "intent": intent,
                "disclaimer": DISCLAIMER_TEXT,
            }

        # Text-to-SQL
        sql_result = generate_sql(question, stock_code)
        sql = sql_result.get("sql", "")
        explanation = sql_result.get("explanation", "")

        if not sql:
            return {
                "answer": "抱歉，我无法理解您的问题，请尝试更具体地描述。",
                "sql_used": None,
                "data": [],
                "intent": intent,
                "disclaimer": DISCLAIMER_TEXT,
            }

        # 执行SQL查询
        try:
            result = self.db.execute(text(sql))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            return {
                "answer": "查询数据时出现错误，请稍后重试或尝试其他问题。",
                "sql_used": sql,
                "data": [],
                "intent": intent,
                "disclaimer": DISCLAIMER_TEXT,
            }

        # 获取对话历史
        history = self._get_chat_history(session_id)

        # 生成回答
        answer_result = generate_answer(
            user_question=question,
            intent=intent,
            sql_query=sql,
            query_result=rows,
            chat_history=history,
        )

        # 保存对话历史
        self._save_chat_history(session_id, question, answer_result["answer"])

        return {
            "answer": answer_result["answer"],
            "sql_used": sql,
            "data": answer_result["data"],
            "intent": intent,
            "disclaimer": DISCLAIMER_TEXT,
        }

    def get_chat_history(self, session_id: str) -> list:
        """获取对话历史"""
        history = self._get_chat_history(session_id)
        return history

    def clear_chat_history(self, session_id: str):
        """清除对话历史"""
        cache_delete(f"chat_history:{session_id}")

    def _get_chat_history(self, session_id: str) -> list:
        """从Redis获取对话历史"""
        data = cache_get(f"chat_history:{session_id}")
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return []
        return []

    def _save_chat_history(self, session_id: str, question: str, answer: str):
        """保存对话历史到Redis"""
        history = self._get_chat_history(session_id)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        # 保留最近20轮对话
        if len(history) > MAX_HISTORY_ROUNDS * 2:
            history = history[-(MAX_HISTORY_ROUNDS * 2):]

        cache_set(f"chat_history:{session_id}", json.dumps(history, ensure_ascii=False), expire=86400)
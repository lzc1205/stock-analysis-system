"""
回答生成与组装
将查询结果和上下文组装成自然语言回答
"""
import json
from ai.llm_client import llm_client
from ai.prompt_templates import ANSWER_GENERATION_PROMPT, DISCLAIMER_TEXT, SYSTEM_PROMPT
from app.utils.logger import logger


def generate_answer(
    user_question: str,
    intent: str,
    sql_query: str,
    query_result: list,
    chat_history: list = None,
) -> dict:
    """
    生成自然语言回答
    :param user_question: 用户原始问题
    :param intent: 意图类型
    :param sql_query: 执行的SQL
    :param query_result: 查询结果数据
    :param chat_history: 对话历史
    :return: {"answer": str, "data": list}
    """
    # 如果没有查询到数据
    if not query_result:
        return {
            "answer": f"抱歉，未查询到相关数据。请检查股票代码是否正确，或尝试调整查询条件。\n\n{DISCLAIMER_TEXT}",
            "data": [],
        }

    # 格式化查询结果
    formatted_result = _format_query_result(query_result)

    prompt = ANSWER_GENERATION_PROMPT.format(
        user_question=user_question,
        intent=intent,
        sql_query=sql_query,
        query_result=formatted_result,
        disclaimer=DISCLAIMER_TEXT,
    )

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if chat_history:
            messages.extend(chat_history[-10:])  # 最多保留最近10轮对话
        messages.append({"role": "user", "content": prompt})

        answer = llm_client.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        return {
            "answer": answer,
            "data": query_result[:20],  # 最多返回20条数据给前端
        }
    except Exception as e:
        logger.error(f"回答生成失败: {e}")
        return {
            "answer": f"查询到 {len(query_result)} 条数据，但AI解读生成失败。\n\n{DISCLAIMER_TEXT}",
            "data": query_result[:20],
        }


def _format_query_result(query_result: list) -> str:
    """格式化查询结果为可读文本"""
    if not query_result:
        return "无数据"

    # 如果结果是dict列表
    if isinstance(query_result[0], dict):
        # 限制最多展示20行
        rows = query_result[:20]
        columns = list(rows[0].keys())
        header = " | ".join(columns)
        separator = "-" * len(header)
        lines = [header, separator]

        for row in rows:
            values = []
            for col in columns:
                val = row.get(col, "")
                if isinstance(val, float):
                    val = f"{val:.2f}"
                values.append(str(val))
            lines.append(" | ".join(values))

        if len(query_result) > 20:
            lines.append(f"... 共 {len(query_result)} 条数据，仅展示前20条")

        return "\n".join(lines)

    return str(query_result)[:2000]
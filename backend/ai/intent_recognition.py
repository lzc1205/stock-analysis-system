"""
意图识别模块
判断用户提问的意图类型
"""
import json
from ai.llm_client import llm_client
from ai.prompt_templates import INTENT_RECOGNITION_PROMPT
from app.utils.logger import logger


def recognize_intent(user_message: str) -> dict:
    """
    识别用户意图
    :param user_message: 用户输入
    :return: {"intent": str, "confidence": float, "entities": dict}
    """
    # 先做关键词匹配，提高效率
    keyword_intent = _keyword_match(user_message)
    if keyword_intent and keyword_intent.get("confidence", 0) > 0.8:
        return keyword_intent

    # 关键词匹配不到，使用大模型
    try:
        prompt = INTENT_RECOGNITION_PROMPT.format(user_message=user_message)
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        result = _parse_json_response(response)
        if result:
            return result
    except Exception as e:
        logger.error(f"意图识别失败: {e}")

    return {"intent": "闲聊", "confidence": 0.5, "entities": {}}


def _keyword_match(user_message: str) -> dict | None:
    """关键词匹配意图"""
    msg = user_message.lower()

    if any(kw in msg for kw in ["价格", "涨跌", "收盘", "开盘", "成交量", "市值", "股价", "多少钱", "涨了", "跌了"]):
        return {"intent": "行情查询", "confidence": 0.9, "entities": {}}

    if any(kw in msg for kw in ["macd", "rsi", "kdj", "均线", "金叉", "死叉", "技术指标", "ma", "布林"]):
        return {"intent": "技术分析", "confidence": 0.9, "entities": {}}

    if any(kw in msg for kw in ["roe", "毛利率", "净利润", "营收", "财务", "资产", "负债", "eps", "每股收益"]):
        return {"intent": "财务分析", "confidence": 0.9, "entities": {}}

    if any(kw in msg for kw in ["资金", "主力", "北向", "散户", "流入", "流出"]):
        return {"intent": "资金流向", "confidence": 0.9, "entities": {}}

    if any(kw in msg for kw in ["行业", "对比", "排名"]):
        return {"intent": "行业对比", "confidence": 0.85, "entities": {}}

    if any(kw in msg for kw in ["买", "卖", "建议", "值得", "适合", "投资"]):
        return {"intent": "投资建议", "confidence": 0.8, "entities": {}}

    return None


def _parse_json_response(response: str) -> dict | None:
    """解析大模型返回的JSON"""
    try:
        # 尝试直接解析
        return json.loads(response)
    except json.JSONDecodeError:
        # 尝试提取JSON块
        import re
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
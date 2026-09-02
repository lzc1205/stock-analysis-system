"""
Text-to-SQL 生成与校验
将自然语言问题转换为 SQL 查询
"""
import json
from datetime import datetime
from ai.llm_client import llm_client
from ai.prompt_templates import TEXT_TO_SQL_PROMPT, TABLE_SCHEMA_DESCRIPTION
from ai.sql_safety import validate_sql, sanitize_sql
from app.utils.logger import logger


def generate_sql(user_question: str, stock_code: str = None) -> dict:
    """
    自然语言转 SQL
    :param user_question: 用户问题
    :param stock_code: 当前关注的股票代码
    :return: {"sql": str, "explanation": str, "confidence": float}
    """
    prompt = TEXT_TO_SQL_PROMPT.format(
        table_schema=TABLE_SCHEMA_DESCRIPTION,
        current_date=datetime.now().strftime("%Y-%m-%d"),
        stock_code=stock_code or "未指定",
        user_question=user_question,
    )

    try:
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )

        result = _parse_response(response)
        if not result:
            return _get_fallback_sql(user_question, stock_code)

        sql = result.get("sql", "")
        is_safe, error_msg = validate_sql(sql)
        if not is_safe:
            logger.warning(f"SQL安全校验失败: {error_msg}")
            return _get_fallback_sql(user_question, stock_code)

        result["sql"] = sanitize_sql(sql)
        return result
    except Exception as e:
        logger.error(f"Text-to-SQL 生成失败: {e}")
        return _get_fallback_sql(user_question, stock_code)


def _get_fallback_sql(user_question: str, stock_code: str) -> dict:
    """当大模型生成SQL失败时，使用规则匹配兜底"""
    explanation = "使用默认查询"
    sql = "SELECT * FROM ads_stock_overview LIMIT 10"

    if stock_code:
        if any(kw in user_question for kw in ["价格", "涨跌", "收盘", "行情"]):
            sql = f"SELECT ts_code, trade_date, close, pct_chg, vol, amount FROM dws_stock_daily_wide WHERE ts_code = '{stock_code}' ORDER BY trade_date DESC LIMIT 10"
            explanation = f"查询 {stock_code} 最近行情数据"
        elif any(kw in user_question for kw in ["macd", "rsi", "kdj", "技术"]):
            sql = f"SELECT ts_code, trade_date, ma5, ma10, ma20, dif, dea, macd_bar, rsi6, k, d, j FROM dws_stock_daily_wide WHERE ts_code = '{stock_code}' ORDER BY trade_date DESC LIMIT 10"
            explanation = f"查询 {stock_code} 技术指标数据"
        elif any(kw in user_question for kw in ["roe", "财务", "利润", "毛利率"]):
            sql = f"SELECT ts_code, end_date, roe, gross_margin, net_margin, revenue_yoy, n_income_yoy, eps FROM ads_financial_health WHERE ts_code = '{stock_code}' ORDER BY end_date DESC LIMIT 10"
            explanation = f"查询 {stock_code} 财务指标数据"

    return {"sql": sql, "explanation": explanation, "confidence": 0.5}


def _parse_response(response: str) -> dict | None:
    """解析大模型返回的结果"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
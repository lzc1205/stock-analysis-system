"""
SQL 安全校验器
确保生成的 SQL 只包含安全的 SELECT 查询
"""
import re
from app.utils.logger import logger


DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE",
    "CREATE", "EXEC", "EXECUTE", "GRANT", "REVOKE",
    "LOAD", "INTO OUTFILE", "INTO DUMPFILE", "SHUTDOWN",
    "RENAME", "REPLACE", "MERGE", "CALL",
]

ALLOWED_TABLES = [
    "ods_stock_daily", "ods_stock_basic", "ods_moneyflow",
    "ods_income", "ods_balancesheet", "ods_cashflow",
    "dwd_stock_daily", "dwd_stock_info", "dwd_financial_indicator",
    "dws_stock_daily_wide", "dws_industry_daily", "dws_stock_weekly",
    "ads_stock_overview", "ads_kline_data", "ads_technical_radar",
    "ads_capital_flow", "ads_financial_health",
]

MAX_QUERY_LIMIT = 100


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    校验SQL安全性
    :param sql: SQL语句
    :return: (是否安全, 错误信息)
    """
    if not sql or not sql.strip():
        return False, "SQL语句为空"

    sql_upper = sql.upper().strip()

    # 必须是SELECT开头
    if not sql_upper.startswith("SELECT"):
        return False, "只允许 SELECT 查询语句"

    # 检查危险关键字
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            return False, f"SQL包含禁止的关键字: {keyword}"

    # 检查是否包含分号（防止多语句注入）
    if ";" in sql.rstrip(";"):
        return False, "不允许执行多条SQL语句"

    # 添加 LIMIT 限制（如果没有）
    if "LIMIT" not in sql_upper:
        sql = f"{sql.strip()} LIMIT {MAX_QUERY_LIMIT}"

    # 检查表名是否在白名单中
    table_pattern = re.compile(r'\bFROM\s+(\w+)', re.IGNORECASE)
    tables = table_pattern.findall(sql)
    for table in tables:
        if table.lower() not in ALLOWED_TABLES:
            return False, f"不允许查询表: {table}"

    return True, ""


def sanitize_sql(sql: str) -> str:
    """
    清理和规范化SQL
    :param sql: 原始SQL
    :return: 清理后的SQL
    """
    # 移除末尾分号
    sql = sql.strip().rstrip(";")

    # 确保有LIMIT
    sql_upper = sql.upper()
    if "LIMIT" not in sql_upper:
        sql = f"{sql} LIMIT {MAX_QUERY_LIMIT}"

    return sql
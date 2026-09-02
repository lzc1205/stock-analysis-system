"""
SQLite -> MySQL 一键迁移
"""
import sqlite3
import pymysql
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "stock_warehouse",
    "charset": "utf8mb4",
}

TABLE_ORDER = [
    "ods_stock_basic", "ods_stock_daily", "ods_daily_basic", "ods_moneyflow",
    "ods_income", "ods_balancesheet", "ods_cashflow",
    "dwd_stock_info", "dwd_stock_daily", "dwd_financial_indicator",
    "dws_stock_daily_wide", "dws_stock_weekly", "dws_industry_daily",
    "ads_stock_overview", "ads_kline_data", "ads_capital_flow",
    "ads_technical_radar", "ads_financial_health",
]

print("=" * 60)
print("SQLite -> MySQL 数据迁移")
print("=" * 60)

sqlite_conn = sqlite3.connect("stock_warehouse.db")
sqlite_conn.row_factory = sqlite3.Row

try:
    mysql_conn = pymysql.connect(**MYSQL_CONFIG)
    print("MySQL 连接成功")
except Exception as e:
    print(f"MySQL 连接失败: {e}")
    print("\n请先确保：")
    print("  1. MySQL 服务已启动")
    print("  2. 数据库 stock_warehouse 已创建（执行 mysql_init.sql）")
    sys.exit(1)

mysql_cursor = mysql_conn.cursor()
mysql_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

for table in TABLE_ORDER:
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = sqlite_cursor.fetchone()[0]
    if row_count == 0:
        print(f"  {table:30s} 空表，跳过")
        continue

    sqlite_cursor.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in sqlite_cursor.description]
    placeholders = ", ".join(["%s"] * len(columns))
    col_names = ", ".join([f"`{c}`" for c in columns])
    insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

    print(f"  {table:30s} {row_count:>8,d} 行...", end=" ", flush=True)

    BATCH_SIZE = 5000
    batch = []
    total_inserted = 0
    for row in sqlite_cursor:
        batch.append(tuple(row))
        if len(batch) >= BATCH_SIZE:
            mysql_cursor.executemany(insert_sql, batch)
            mysql_conn.commit()
            total_inserted += len(batch)
            batch = []
    if batch:
        mysql_cursor.executemany(insert_sql, batch)
        mysql_conn.commit()
        total_inserted += len(batch)

    print(f"√ 已导入 {total_inserted:,d} 行")

mysql_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
mysql_conn.close()
sqlite_conn.close()
print("\n" + "=" * 60)
print("迁移完成！")
print("=" * 60)
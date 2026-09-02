"""
定时调度模块
基于 APScheduler 实现数据采集、ETL 流程的定时自动化

策略：
1. 历史数据一次性导入：run_historical_collect() 多线程跑全量
2. 每日增量采集：run_daily_collect() 只拉最近 2 天
3. 本地缓存：INSERT OR IGNORE 避免重复入库
4. 数据源：新浪 API（纯 HTTP REST，支持多线程）
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from app.utils.logger import logger
from app.config import settings

scheduler = BackgroundScheduler()


def start_scheduler():
    """启动定时任务调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已停止")


def add_daily_collect_job():
    """添加每日数据采集任务"""
    scheduler.add_job(
        func=run_daily_collect,
        trigger=CronTrigger(hour=settings.collect_hour, minute=settings.collect_minute),
        id="daily_collect",
        name="每日数据采集",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info(f"已添加每日数据采集任务，执行时间：{settings.collect_hour}:{settings.collect_minute:02d}")


def add_etl_job():
    """添加每日ETL任务"""
    etl_hour = settings.collect_hour + 1
    if etl_hour >= 24:
        etl_hour = 0
    scheduler.add_job(
        func=run_daily_etl,
        trigger=CronTrigger(hour=etl_hour, minute=30),
        id="daily_etl",
        name="每日ETL",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info(f"已添加每日ETL任务，执行时间：{etl_hour}:30")


# ============================================================
# 股票列表获取（仅一次，内存缓存）
# ============================================================
_stock_cache = None


def _get_stock_list():
    """获取A股个股列表（带缓存，新浪API）"""
    global _stock_cache
    if _stock_cache is not None:
        return _stock_cache

    from collector.sina_collector import SinaCollector
    sina = SinaCollector()
    df = sina.get_stock_list()
    if df.empty:
        logger.error("新浪获取股票列表失败")
        return []

    stocks_data = df.to_dict("records")
    _stock_cache = stocks_data
    logger.info(f"股票列表缓存: {len(stocks_data)} 只")
    return stocks_data


# ============================================================
# 数据源采集函数
# ============================================================
def _collect_from_sina(ts_code, start_date, end_date):
    """从新浪采集"""
    from collector.sina_collector import SinaCollector
    sina = SinaCollector()
    return sina.get_daily_kline(ts_code, start_date=start_date, end_date=end_date)


def _collect_with_fallback(ts_code, start_date, end_date):
    """多数据源轮换采集（新浪优先）"""
    df = _collect_from_sina(ts_code, start_date, end_date)
    if not df.empty:
        return df, "sina"

    return df, None


# ============================================================
# 批量入库
# ============================================================
def _batch_insert_daily(records_batch):
    """批量插入日线数据"""
    from app.utils.database import SessionLocal
    from sqlalchemy import text
    from app.utils.logger import logger

    db = SessionLocal()
    try:
        db.execute(
            text("""INSERT OR IGNORE INTO ods_stock_daily
                (ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount, turn, source)
                VALUES (:ts_code, :trade_date, :open, :high, :low, :close, :pre_close, :change, :pct_chg, :vol, :amount, :turn, :source)"""),
            records_batch,
        )
        db.commit()
    except Exception as e:
        logger.error(f"批量入库失败: {e}")
    finally:
        db.close()


def _batch_insert_stock_basic(stocks_data):
    """批量插入股票基本信息"""
    from app.utils.database import SessionLocal
    from sqlalchemy import text
    from app.utils.logger import logger

    db = SessionLocal()
    try:
        existing = set(r[0] for r in db.execute(
            text("SELECT ts_code FROM ods_stock_basic")
        ).fetchall())
        new_stocks = [s for s in stocks_data if s["ts_code"] not in existing]
        if new_stocks:
            db.execute(
                text("INSERT INTO ods_stock_basic (ts_code, symbol, name, market) VALUES (:ts_code, :symbol, :name, :market)"),
                new_stocks,
            )
            db.commit()
            logger.info(f"股票基本信息入库: {len(new_stocks)} 只")
    finally:
        db.close()


# ============================================================
# 历史数据一次性导入（全量）
# ============================================================
def run_historical_collect(days=365, limit=None, max_workers=4):
    """
    历史数据一次性导入
    新浪API纯HTTP，支持多线程并发，4线程安全
    """
    logger.info(f"===== 历史数据导入开始（{days}天，{max_workers}线程）=====")
    stocks_data = _get_stock_list()
    if limit:
        stocks_data = stocks_data[:limit]
    total = len(stocks_data)

    _batch_insert_stock_basic(stocks_data)

    today = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    batch_records = []
    batch_size = 500
    collected = 0
    failed = 0
    lock = Lock()

    def _collect_one(stock_info):
        ts_code = stock_info["ts_code"]
        try:
            df, source = _collect_with_fallback(ts_code, start_date, today)
            if df.empty:
                return None

            records = []
            for _, row in df.iterrows():
                records.append({
                    "ts_code": row.get("ts_code"),
                    "trade_date": row.get("trade_date"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "pre_close": row.get("pre_close"),
                    "change": row.get("change"),
                    "pct_chg": row.get("pct_chg"),
                    "vol": row.get("vol"),
                    "amount": row.get("amount"),
                    "turn": row.get("turn"),
                    "source": source,
                })
            return records
        except Exception as e:
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_collect_one, s) for s in stocks_data]

        for future in as_completed(futures):
            records = future.result()
            if records:
                with lock:
                    batch_records.extend(records)
                    collected += 1
                    if len(batch_records) >= batch_size:
                        _batch_insert_daily(batch_records)
                        batch_records = []
                    if collected % 100 == 0:
                        logger.info(f"历史导入进度: {collected}/{total} (失败: {failed})")
            else:
                with lock:
                    failed += 1

    if batch_records:
        _batch_insert_daily(batch_records)

    logger.info(f"===== 历史数据导入完成，成功 {collected} 只，失败 {failed} 只 =====")


# ============================================================
# 每日增量采集
# ============================================================
def run_daily_collect():
    """
    每日增量采集
    只拉最近 2 天的数据，库里有就不请求
    """
    logger.info("开始增量采集...")
    stocks_data = _get_stock_list()
    _batch_insert_stock_basic(stocks_data)

    today = datetime.now().strftime("%Y-%m-%d")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    batch_records = []
    batch_size = 500
    collected = 0
    failed = 0
    total = len(stocks_data)

    for i, stock_info in enumerate(stocks_data):
        ts_code = stock_info["ts_code"]
        try:
            df, source = _collect_with_fallback(ts_code, two_days_ago, today)
            if df.empty:
                continue

            for _, row in df.iterrows():
                batch_records.append({
                    "ts_code": row.get("ts_code"),
                    "trade_date": row.get("trade_date"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "pre_close": row.get("pre_close"),
                    "change": row.get("change"),
                    "pct_chg": row.get("pct_chg"),
                    "vol": row.get("vol"),
                    "amount": row.get("amount"),
                    "turn": row.get("turn"),
                    "source": source,
                })

            collected += 1

            if len(batch_records) >= batch_size:
                _batch_insert_daily(batch_records)
                batch_records = []

            if collected % 100 == 0:
                logger.info(f"增量采集进度: {collected}/{total}")

        except Exception as e:
            failed += 1
            if failed % 100 == 0:
                logger.error(f"采集 {ts_code} 失败: {e}")

    if batch_records:
        _batch_insert_daily(batch_records)

    logger.info(f"增量采集完成，成功 {collected} 只，失败 {failed} 只")


def run_daily_etl():
    """执行每日ETL流程"""
    logger.info("开始执行每日ETL...")
    try:
        from etl.ods_to_dwd import run_ods_to_dwd
        from etl.dwd_to_dws import run_dwd_to_dws
        from etl.dws_to_ads import run_dws_to_ads

        run_ods_to_dwd()
        run_dwd_to_dws()
        run_dws_to_ads()

        logger.info("每日ETL完成")
    except Exception as e:
        logger.error(f"每日ETL异常: {e}")


def init_scheduler():
    """初始化调度器"""
    start_scheduler()
    add_daily_collect_job()
    add_etl_job()
    logger.info("定时任务调度器初始化完成")
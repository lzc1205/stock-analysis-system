"""
批量采集更多股票的K线数据
使用新浪财经API，支持增量采集
"""
import time
from datetime import datetime, timedelta
from collector.sina_collector import SinaCollector
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger


def batch_collect_kline(max_stocks: int = 500, delay: float = 0.3):
    """
    批量采集K线数据
    :param max_stocks: 最大采集数量
    :param delay: 请求间隔(秒)
    """
    db = SessionLocal()
    c = SinaCollector()

    try:
        # 获取所有股票代码
        all_stocks = c.get_stock_list()
        if all_stocks.empty:
            logger.error("无法获取股票列表")
            return

        # 找出还没有K线数据的股票
        existing = set()
        result = db.execute(text('SELECT DISTINCT ts_code FROM dws_stock_daily_wide')).fetchall()
        for row in result:
            existing.add(row[0])

        # 过滤出需要采集的股票
        need_collect = []
        for _, row in all_stocks.iterrows():
            ts_code = row['ts_code']
            if ts_code not in existing:
                need_collect.append(ts_code)

        # 限制数量
        if max_stocks:
            need_collect = need_collect[:max_stocks]

        total = len(need_collect)
        logger.info(f"需要采集 {total} 只股票的K线数据")

        success = 0
        fail = 0

        for i, ts_code in enumerate(need_collect):
            try:
                # 采集120天K线
                df = c.get_daily_kline(ts_code, datalen=120)
                if df.empty:
                    fail += 1
                    continue

                # 保存到ODS层
                for _, row in df.iterrows():
                    sql = text("""
                        INSERT OR IGNORE INTO ods_stock_daily 
                            (ts_code, trade_date, open, high, low, close, pre_close,
                             change, pct_chg, vol, amount, turn, source)
                        VALUES (:ts_code, :trade_date, :open, :high, :low, :close,
                                :pre_close, :change, :pct_chg, :vol, :amount, :turn, :source)
                    """)
                    db.execute(sql, {
                        'ts_code': row.get('ts_code', ts_code),
                        'trade_date': str(row.get('trade_date', '')),
                        'open': float(row.get('open', 0) or 0),
                        'high': float(row.get('high', 0) or 0),
                        'low': float(row.get('low', 0) or 0),
                        'close': float(row.get('close', 0) or 0),
                        'pre_close': float(row.get('pre_close', 0) or 0),
                        'change': float(row.get('change', 0) or 0),
                        'pct_chg': float(row.get('pct_chg', 0) or 0),
                        'vol': float(row.get('vol', 0) or 0),
                        'amount': float(row.get('amount', 0) or 0),
                        'turn': float(row.get('turn', 0) or 0),
                        'source': 'sina',
                    })

                db.commit()
                success += 1

                # 每50只提交一次进度
                if (success + fail) % 50 == 0:
                    logger.info(f"进度: {success + fail}/{total}, 成功: {success}, 失败: {fail}")

            except Exception as e:
                fail += 1
                logger.warning(f"[{i+1}/{total}] {ts_code} 失败: {e}")

            time.sleep(delay)

        logger.info(f"采集完成! 成功: {success}, 失败: {fail}")

    finally:
        db.close()


if __name__ == "__main__":
    import sys
    max_stocks = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    print(f"开始采集 {max_stocks} 只股票的K线数据...")
    batch_collect_kline(max_stocks=max_stocks)
    print("采集完成!")
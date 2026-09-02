"""
同花顺数据每日同步脚本
从同花顺API获取全市场A股快照数据，更新ODS层，触发ETL流程
"""
import sys
import time
from datetime import datetime

from app.utils.logger import logger
from app.utils.database import SessionLocal
from collector.ths_collector import THSCollector


def sync_daily_snapshot():
    """同步每日快照数据"""
    logger.info("=" * 50)
    logger.info(f"开始同花顺数据同步  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    db = SessionLocal()
    collector = THSCollector()

    try:
        # Step 1: 获取全市场快照数据
        logger.info("Step 1: 获取全市场A股快照数据...")
        df = collector.get_snapshot()
        if df.empty:
            logger.error("快照数据为空，同步终止")
            return

        logger.info(f"获取到 {len(df)} 只股票行情数据")

        # Step 2: 保存到 ODS 层
        logger.info("Step 2: 保存快照数据到 ods_stock_daily...")
        count = collector.save_snapshot_to_db(db, df)
        logger.info(f"ODS层更新: {count} 条记录")

        # Step 3: 运行 ETL 流程
        logger.info("Step 3: 运行 ODS -> DWD ETL...")
        from etl.ods_to_dwd import run_ods_to_dwd
        run_ods_to_dwd()

        logger.info("Step 4: 运行 DWD -> DWS ETL...")
        from etl.dwd_to_dws import run_dwd_to_dws
        run_dwd_to_dws()

        logger.info("Step 5: 运行 DWS -> ADS ETL...")
        from etl.dws_to_ads import run_dws_to_ads
        run_dws_to_ads()

        logger.info("=" * 50)
        logger.info("同花顺数据同步完成!")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"同步过程异常: {e}")
        db.rollback()
    finally:
        db.close()


def sync_historical_kline(ts_codes: list = None, days: int = 365):
    """
    同步历史K线数据（备选方案，当API支持时使用）
    """
    db = SessionLocal()
    collector = THSCollector()

    if ts_codes is None:
        stock_df = collector.get_stock_list()
        ts_codes = stock_df["ts_code"].tolist()[:100]  # 默认只取前100只

    try:
        from app.models.ods import OdsStockDaily

        for ts_code in ts_codes:
            try:
                df = collector.get_historical_kline(ts_code, start_date=None, end_date=None)
                if df.empty:
                    continue

                for _, row in df.iterrows():
                    try:
                        existing = db.query(OdsStockDaily).filter(
                            OdsStockDaily.ts_code == row["ts_code"],
                            OdsStockDaily.trade_date == row["trade_date"]
                        ).first()
                        if not existing:
                            record = OdsStockDaily(
                                ts_code=row["ts_code"],
                                trade_date=datetime.strptime(str(row["trade_date"]), "%Y%m%d").date(),
                                open=row.get("open"),
                                high=row.get("high"),
                                low=row.get("low"),
                                close=row.get("close"),
                                pre_close=row.get("pre_close"),
                                change=row.get("change"),
                                pct_chg=row.get("pct_chg"),
                                vol=row.get("vol"),
                                amount=row.get("amount"),
                                turn=row.get("turn", 0),
                                source="ths",
                            )
                            db.add(record)
                    except Exception:
                        continue

                db.commit()
                logger.info(f"K线 {ts_code}: {len(df)} 条")

                time.sleep(0.5)  # 避免限流

            except Exception as e:
                logger.warning(f"K线 {ts_code} 失败: {e}")
                continue

    except Exception as e:
        logger.error(f"历史K线同步失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="同花顺数据同步")
    parser.add_argument("--mode", choices=["daily", "history", "all"], default="daily",
                        help="同步模式: daily=每日快照, history=历史K线(暂不可用), all=全部")
    parser.add_argument("--skip-etl", action="store_true", help="跳过ETL流程")
    args = parser.parse_args()

    if args.mode == "daily":
        sync_daily_snapshot()
    elif args.mode == "history":
        sync_historical_kline()
    elif args.mode == "all":
        sync_daily_snapshot()
        sync_historical_kline()
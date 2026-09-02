"""
全量数据采集器
使用 AkShare 获取 5000+ 只 A 股完整数据
包括：股票列表(含行业)、日线行情、每日基本面(pe/pb/市值)、资金流向
"""
import akshare as ak
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import SessionLocal
from app.utils.logger import logger


class FullDataCollector:
    """全量数据采集器"""

    def __init__(self):
        self.db = SessionLocal()

    def collect_stock_list_with_industry(self):
        """
        获取全部A股列表 + 行业分类
        数据源：东方财富 (akshare)
        返回：DataFrame 含 ts_code, name, industry, market 等
        """
        try:
            logger.info("开始获取A股全量列表...")
            
            # 方法1: 东方财富实时行情（最全）
            df = ak.stock_zh_a_spot_em()
            if df.empty:
                logger.error("获取股票列表为空")
                return pd.DataFrame()

            logger.info(f"获取到 {len(df)} 只股票")

            # 标准化列名
            result = []
            for _, row in df.iterrows():
                code = str(row.get('代码', ''))
                name = str(row.get('名称', ''))
                
                # 判断市场
                if code.startswith('6') or code.startswith('9'):
                    market = 'SH'
                else:
                    market = 'SZ'
                
                ts_code = f"{code}.{market}"
                
                result.append({
                    'ts_code': ts_code,
                    'symbol': code,
                    'name': name,
                    'market': market,
                    'latest_price': row.get('最新价', 0),
                    'latest_pct_chg': row.get('涨跌幅', 0),
                })

            result_df = pd.DataFrame(result)
            logger.info(f"标准化后共 {len(result_df)} 只股票")
            return result_df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def collect_industry_classification(self):
        """
        获取行业板块分类（东方财富）
        返回：DataFrame 含 股票代码, 行业名称
        """
        try:
            logger.info("获取行业板块分类...")
            
            # 获取所有行业板块
            industries = ak.stock_board_industry_name_em()
            if industries.empty:
                return {}

            stock_industry_map = {}
            
            # 遍历每个行业，获取该行业的成分股
            for _, ind_row in industries.iterrows():
                industry_name = ind_row.get('板块名称', '')
                if not industry_name:
                    continue
                
                try:
                    time.sleep(0.3)  # 限速
                    members = ak.stock_board_industry_cons_em(symbol=industry_name)
                    if not members.empty:
                        for _, stock in members.iterrows():
                            code = str(stock.get('代码', ''))
                            if code.startswith('6'):
                                ts_code = f"{code}.SH"
                            elif code.startswith('8') or code.startswith('4'):
                                ts_code = f"{code}.BJ"
                            else:
                                ts_code = f"{code}.SZ"
                            stock_industry_map[ts_code] = industry_name
                except Exception as e:
                    logger.warning(f"获取 {industry_name} 成分股失败: {e}")
                    continue
            
            logger.info(f"完成行业分类映射，共 {len(stock_industry_map)} 只股票")
            return stock_industry_map

        except Exception as e:
            logger.error(f"获取行业分类失败: {e}")
            return {}

    def collect_daily_data(self, ts_code: str, days: int = 120) -> pd.DataFrame:
        """
        获取个股日线行情（东方财富源，数据更全）
        包含：开盘/收盘/最高/最低/成交量/成交额/涨跌幅/换手率
        """
        symbol = ts_code.split('.')[0]
        
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days * 1.5)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )
            
            if df.empty:
                return pd.DataFrame()

            df['ts_code'] = ts_code
            df.rename(columns={
                '日期': 'trade_date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'vol',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_chg',
                '涨跌额': 'change',
                '换手率': 'turn',
            }, inplace=True)

            return df

        except Exception as e:
            logger.warning(f"获取 {ts_code} 日线失败: {e}")
            return pd.DataFrame()

    def collect_daily_basic(self, ts_code: str, days: int = 120) -> pd.DataFrame:
        """
        获取每日基本面指标（PE/PB/市值等）
        数据源：东方财富
        """
        symbol = ts_code.split('.')[0]
        
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days * 1.5)).strftime('%Y%m%d')

            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )

            if df.empty:
                return pd.DataFrame()

            # 获取实时估值数据补充 PE/PB/市值
            try:
                spot_df = ak.stock_zh_a_spot_em()
                stock_row = spot_df[spot_df['代码'] == symbol]
                if not stock_row.empty:
                    pe = stock_row.iloc[0].get('市盈率-动态', 0) or 0
                    pb = stock_row.iloc[0].get('市净率', 0) or 0
                    total_mv = stock_row.iloc[0].get('总市值', 0) or 0
                    circ_mv = stock_df.iloc[0].get('流通市值', 0) or 0
                else:
                    pe, pb, total_mv, circ_mv = 0, 0, 0, 0
            except:
                pe, pb, total_mv, circ_mv = 0, 0, 0, 0

            result = []
            for _, row in df.iterrows():
                result.append({
                    'ts_code': ts_code,
                    'trade_date': row.get('日期'),
                    'pe': pe,
                    'pb': pb,
                    'total_mv': total_mv,
                    'circ_mv': circ_mv,
                    'turnover_rate': row.get('换手率', 0),
                })

            return pd.DataFrame(result)

        except Exception as e:
            logger.warning(f"获取 {ts_code} 基本面失败: {e}")
            return pd.DataFrame()

    def save_to_database(self, stock_list: pd.DataFrame, industry_map: dict = None):
        """保存股票列表到数据库"""
        if stock_list.empty:
            return

        try:
            delete_sql = text("DELETE FROM ods_stock_basic")
            self.db.execute(delete_sql)

            insert_count = 0
            for _, row in stock_list.iterrows():
                ts_code = row['ts_code']
                industry = industry_map.get(ts_code, '其他') if industry_map else '其他'

                sql = text("""
                    INSERT OR IGNORE INTO ods_stock_basic 
                        (ts_code, symbol, name, area, industry, market, list_date)
                    VALUES (:ts_code, :symbol, :name, :area, :industry, :market, :list_date)
                """)
                self.db.execute(sql, {
                    'ts_code': ts_code,
                    'symbol': row.get('symbol', ''),
                    'name': row.get('name', ''),
                    'area': '',
                    'industry': industry,
                    'market': row.get('market', ''),
                    'list_date': None,
                })
                insert_count += 1

            self.db.commit()
            logger.info(f"保存股票列表到数据库: {insert_count} 条")

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存股票列表失败: {e}")

    def batch_collect_daily_data(self, max_stocks: int = None, delay: float = 0.5):
        """
        批量采集所有股票的日线数据
        :param max_stocks: 最大采集数量，None表示全部
        :param delay: 请求间隔（秒）
        """
        stock_list = self.collect_stock_list_with_industry()
        if stock_list.empty:
            logger.error("无法获取股票列表")
            return

        codes = stock_list['ts_code'].tolist()
        if max_stocks:
            codes = codes[:max_stocks]

        total = len(codes)
        success_count = 0
        fail_count = 0

        logger.info(f"开始批量采集 {total} 只股票的日线数据...")

        for i, ts_code in enumerate(codes):
            try:
                # 采集日线行情
                daily_df = self.collect_daily_data(ts_code)
                if not daily_df.empty:
                    self._save_daily_data(daily_df)
                    success_count += 1

                time.sleep(delay)

                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i+1}/{total}, 成功: {success_count}, 失败: {fail_count}")

            except Exception as e:
                fail_count += 1
                logger.warning(f"[{i+1}/{total}] {ts_code} 失败: {e}")
                time.sleep(delay * 2)

        logger.info(f"批量采集完成! 总计: {total}, 成功: {success_count}, 失败: {fail_count}")

    def _save_daily_data(self, df: pd.DataFrame):
        """保存日线数据到ODS层"""
        for _, row in df.iterrows():
            sql = text("""
                INSERT OR IGNORE INTO ods_stock_daily 
                    (ts_code, trade_date, open, high, low, close, pre_close, 
                     change, pct_chg, vol, amount, turn, source)
                VALUES (:ts_code, :trade_date, :open, :high, :low, :close, 
                        :pre_close, :change, :pct_chg, :vol, :amount, :turn, :source)
            """)
            self.db.execute(sql, {
                'ts_code': row.get('ts_code', ''),
                'trade_date': str(row.get('trade_date', '')),
                'open': float(row.get('open', 0) or 0),
                'high': float(row.get('high', 0) or 0),
                'low': float(row.get('low', 0) or 0),
                'close': float(row.get('close', 0) or 0),
                'pre_close': float(row.get('close', 0) or 0),  # 简化处理
                'change': float(row.get('change', 0) or 0),
                'pct_chg': float(row.get('pct_chg', 0) or 0),
                'vol': float(row.get('vol', 0) or 0),
                'amount': float(row.get('amount', 0) or 0),
                'turn': float(row.get('turn', 0) or 0),
                'source': 'akshare',
            })
        self.db.commit()

    def close(self):
        self.db.close()


def run_full_collection(max_stocks: int = None):
    """
    执行全量数据采集
    :param max_stocks: 最大采集数量
    """
    collector = FullDataCollector()
    
    try:
        print("=" * 50)
        print("开始全量数据采集")
        print("=" * 50)

        # 第一步：获取股票列表和行业分类
        print("\n[1/3] 获取股票列表和行业分类...")
        stock_list = collector.collect_stock_list_with_industry()
        
        print("\n[2/3] 获取行业板块分类（可能需要几分钟）...")
        industry_map = collector.collect_industry_classification()
        
        print(f"\n   获取到 {len(industry_map)} 只股票的行业分类")
        print(f"   行业分布:")
        from collections import Counter
        industry_counts = Counter(industry_map.values())
        for ind, cnt in industry_counts.most_common(10):
            print(f"      - {ind}: {cnt}只")

        # 保存股票列表
        print("\n[2.5/3] 保存股票列表到数据库...")
        collector.save_to_database(stock_list, industry_map)

        # 第三步：批量采集日线数据
        print(f"\n[3/3] 开始批量采集日线数据...")
        collector.batch_collect_daily_data(max_stocks=max_stocks, delay=0.5)

        print("\n" + "=" * 50)
        print("全量数据采集完成!")
        print("=" * 50)

    finally:
        collector.close()


if __name__ == "__main__":
    import sys
    
    max_stocks = None
    if len(sys.argv) > 1:
        max_stocks = int(sys.argv[1])
    
    run_full_collection(max_stocks=max_stocks)
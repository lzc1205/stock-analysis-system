"""
全面多源数据采集器
整合 AkShare + 新浪财经 + 东方财富 等多个数据源
覆盖 5000+ A股全市场数据，包含各行各业

数据类型：
1. 股票基础信息（代码、名称、行业、上市日期等）
2. 日线/周线/月线行情（开高低收、成交量、涨跌幅等）
3. 财务数据（营收、利润、资产负债、现金流等）
4. 资金流向（主力资金、散户资金、北向资金等）
5. 行业板块分类（109个细分行业）
6. 股东信息（股东户数、户均持股等）
7. 技术指标（MA/MACD/RSI/KDJ等）
8. 估值数据（PE/PB/PS/市值等）

使用方式：
    from collector.comprehensive_collector import ComprehensiveCollector
    
    cc = ComprehensiveCollector()
    
    # 采集全量数据（首次运行，约需2-3小时）
    cc.collect_all_stocks_full(max_stocks=5000)
    
    # 每日增量更新（每天运行一次，约需30分钟）
    cc.daily_incremental_update()
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import SessionLocal
from app.utils.logger import logger


class ComprehensiveCollector:
    """全面多源数据采集器"""

    def __init__(self):
        self.db = SessionLocal()
        self.delay_range = (0.3, 0.8)  # 随机延迟范围，避免被封
        self.max_retries = 3  # 最大重试次数

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def _random_delay(self):
        """随机延迟，避免请求过快"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def _safe_request(self, func, *args, **kwargs):
        """安全的请求封装，带重试机制"""
        for i in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                if result is not None and (not isinstance(result, pd.DataFrame) or not result.empty):
                    return result
                if i < self.max_retries - 1:
                    time.sleep(2 ** i)  # 指数退避
            except Exception as e:
                logger.warning(f"请求失败 (第{i+1}次): {e}")
                if i < self.max_retries - 1:
                    time.sleep(2 ** i)
        return None

    # ==================== 1. 股票基础信息 ====================
    
    def get_all_stock_list(self) -> pd.DataFrame:
        """
        获取全部A股列表（5000+只）
        数据源：东方财富实时行情
        返回：ts_code, symbol, name, market, industry 等
        """
        try:
            logger.info("获取全部A股股票列表...")
            
            df = ak.stock_zh_a_spot_em()
            if df.empty:
                logger.error("股票列表为空")
                return pd.DataFrame()

            result = []
            for _, row in df.iterrows():
                code = str(row.get('代码', '')).zfill(6)
                name = str(row.get('名称', ''))
                
                # 判断市场
                if code.startswith(('6', '9')):
                    market = 'SH'
                elif code.startswith(('8', '4')):
                    market = 'BJ'
                else:
                    market = 'SZ'
                
                ts_code = f"{code}.{market}"
                
                result.append({
                    'ts_code': ts_code,
                    'symbol': code,
                    'name': name,
                    'market': market,
                    'price': row.get('最新价', 0),
                    'pct_chg': row.get('涨跌幅', 0),
                    'volume': row.get('成交量', 0),
                    'amount': row.get('成交额', 0),
                    'turnover': row.get('换手率', 0),
                    'pe': row.get('市盈率-动态', 0),
                    'pb': row.get('市净率', 0),
                    'total_mv': row.get('总市值', 0),
                    'circ_mv': row.get('流通市值', 0),
                    'rise_speed': row.get('涨速', 0),
                    'high_52w': row.get('年内最高', 0),
                    'low_52w': row.get('年内最低', 0),
                })

            result_df = pd.DataFrame(result)
            logger.info(f"成功获取 {len(result_df)} 只A股股票")
            return result_df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_industry_classification(self) -> Dict[str, str]:
        """
        获取完整的行业板块分类（109个细分行业）
        返回：{ts_code: industry_name} 映射
        """
        try:
            logger.info("获取行业板块分类...")
            
            industries = ak.stock_board_industry_name_em()
            if industries.empty:
                return {}

            stock_industry_map = {}
            total_industries = len(industries)
            
            for idx, (_, ind_row) in enumerate(industries.iterrows()):
                industry_name = ind_row.get('板块名称', '')
                if not industry_name:
                    continue
                
                try:
                    self._random_delay()
                    
                    # 获取该行业的成分股
                    members = ak.stock_board_industry_cons_em(symbol=industry_name)
                    if not members.empty:
                        for _, stock in members.iterrows():
                            code = str(stock.get('代码', '')).zfill(6)
                            if code.startswith(('6', '9')):
                                ts_code = f"{code}.SH"
                            elif code.startswith(('8', '4')):
                                ts_code = f"{code}.BJ"
                            else:
                                ts_code = f"{code}.SZ"
                            stock_industry_map[ts_code] = industry_name
                    
                    if (idx + 1) % 20 == 0:
                        logger.info(f"行业分类进度: {idx+1}/{total_industries}, 已映射 {len(stock_industry_map)} 只股票")
                        
                except Exception as e:
                    logger.warning(f"获取 {industry_name} 成分股失败: {e}")
                    continue
            
            logger.info(f"完成行业分类，共 {len(stock_industry_map)} 只股票, {len(set(stock_industry_map.values()))} 个行业")
            return stock_industry_map

        except Exception as e:
            logger.error(f"获取行业分类失败: {e}")
            return {}

    def get_concept_classification(self) -> Dict[str, List[str]]:
        """
        获取概念板块分类
        返回：{ts_code: [concept1, concept2, ...]}
        """
        try:
            logger.info("获取概念板块分类...")
            
            concepts = ak.stock_board_concept_name_em()
            if concepts.empty:
                return {}

            stock_concept_map = {}
            
            for _, con_row in concepts.iterrows():
                concept_name = con_row.get('板块名称', '')
                if not concept_name:
                    continue
                
                try:
                    self._random_delay()
                    members = ak.stock_board_concept_cons_em(symbol=concept_name)
                    if not members.empty:
                        for _, stock in members.iterrows():
                            code = str(stock.get('代码', '')).zfill(6)
                            if code.startswith(('6', '9')):
                                ts_code = f"{code}.SH"
                            elif code.startswith(('8', '4')):
                                ts_code = f"{code}.BJ"
                            else:
                                ts_code = f"{code}.SZ"
                            
                            if ts_code not in stock_concept_map:
                                stock_concept_map[ts_code] = []
                            stock_concept_map[ts_code].append(concept_name)
                except:
                    continue
            
            logger.info(f"完成概念分类，共 {len(stock_concept_map)} 只股票有概念标签")
            return stock_concept_map

        except Exception as e:
            logger.error(f"获取概念分类失败: {e}")
            return {}

    # ==================== 2. 日线行情数据 ====================
    
    def get_stock_daily_kline(self, ts_code: str, days: int = 365, adjust: str = "qfq") -> pd.DataFrame:
        """
        获取个股日线行情
        :param ts_code: 股票代码 600000.SH
        :param days: 获取天数
        :param adjust: 复权类型 qfq/hfq/空
        """
        symbol = ts_code.split('.')[0]
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=int(days * 1.5))).strftime('%Y%m%d')
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
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
            
            return df[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 
                      'pre_close', 'change', 'pct_chg', 'vol', 'amount', 
                      'turn', 'amplitude']]
            
        except Exception as e:
            logger.error(f"获取 {ts_code} 日线失败: {e}")
            return pd.DataFrame()

    def get_stock_weekly_kline(self, ts_code: str, weeks: int = 52) -> pd.DataFrame:
        """获取周线数据"""
        symbol = ts_code.split('.')[0]
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="weekly",
                adjust="qfq"
            )
            
            if not df.empty:
                df['ts_code'] = ts_code
                df.rename(columns={
                    '日期': 'trade_date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'vol',
                    '成交额': 'amount',
                    '涨跌幅': 'pct_chg',
                    '换手率': 'turn',
                }, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取 {ts_code} 周线失败: {e}")
            return pd.DataFrame()

    # ==================== 3. 财务数据 ====================
    
    def get_stock_financial(self, ts_code: str) -> pd.DataFrame:
        """
        获取股票财务数据（利润表、资产负债表、现金流表）
        """
        symbol = ts_code.split('.')[0]
        
        try:
            # 利润表
            profit = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按年度")
            
            # 主要财务指标
            indicator = ak.stock_financial_analysis_indicator(symbol=symbol)
            
            result = {
                'ts_code': ts_code,
                'collect_time': datetime.now(),
            }
            
            if not profit.empty and len(profit) > 0:
                latest = profit.iloc[0]
                result.update({
                    'revenue': latest.get('营业收入', 0),
                    'net_profit': latest.get('净利润', 0),
                    'gross_profit_margin': latest.get('销售毛利率', 0),
                    'net_profit_margin': latest.get('销售净利率', 0),
                    'roe': latest.get('净资产收益率', 0),
                    'roa': latest.get('总资产收益率', 0),
                })
            
            if not indicator.empty and len(indicator) > 0:
                latest = indicator.iloc[0]
                result.update({
                    'eps': latest.get('每股收益', 0),
                    'bps': latest.get('每股净资产', 0),
                    'cfps': latest.get('每股经营现金流', 0),
                    'debt_ratio': latest.get('资产负债率', 0),
                    'current_ratio': latest.get('流动比率', 0),
                    'quick_ratio': latest.get('速动比率', 0),
                })
            
            return pd.DataFrame([result])
            
        except Exception as e:
            logger.error(f"获取 {ts_code} 财务数据失败: {e}")
            return pd.DataFrame()

    def get_stock_valuation(self, ts_code: str) -> pd.DataFrame:
        """获取估值数据（PE/PB/PS等）"""
        symbol = ts_code.split('.')[0]
        
        try:
            df = ak.stock_zh_a_spot_em()  # 实时行情中包含估值数据
            stock_row = df[df['代码'] == symbol]
            
            if not stock_row.empty:
                row = stock_row.iloc[0]
                return pd.DataFrame([{
                    'ts_code': ts_code,
                    'pe_dynamic': row.get('市盈率-动态', 0),
                    'pe_static': row.get('市盈率-静态', 0),
                    'pb': row.get('市净率', 0),
                    'ps': row.get('市销率', 0),
                    'total_mv': row.get('总市值', 0),
                    'circ_mv': row.get('流通市值', 0),
                    'collect_time': datetime.now(),
                }])
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取 {ts_code} 估值数据失败: {e}")
            return pd.DataFrame()

    # ==================== 4. 资金流向 ====================
    
    def get_money_flow_individual(self, ts_code: str) -> pd.DataFrame:
        """
        获取个股资金流向
        主力资金、超大单、大单、中单、小单
        """
        symbol = ts_code.split('.')[0]
        market = 'sh' if ts_code.endswith('.SH') else 'sz'
        
        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
            
            if df.empty:
                return pd.DataFrame()

            df['ts_code'] = ts_code
            df.rename(columns={
                '日期': 'date',
                '主力净流入-净额': 'main_net_inflow',
                '主力净流入-净占比': 'main_net_pct',
                '超大单净流入-净额': 'super_large_net',
                '大单净流入-净额': 'large_net',
                '中单净流入-净额': 'medium_net',
                '小单净流入-净额': 'small_net',
            }, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取 {ts_code} 资金流向失败: {e}")
            return pd.DataFrame()

    def get_north_money_flow(self) -> pd.DataFrame:
        """获取北向资金流向（每日）"""
        try:
            df = ak.stock_hsgt_fund_flow_summary_em(symbol="北上")
            
            if not df.empty:
                df['source'] = 'north'
                df.rename(columns={
                    '日期': 'date',
                    '当日净流入': 'net_inflow',
                    '当日成交净买额': 'net_buy',
                    '历史累计净买入': 'cumulative_buy',
                }, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
            return pd.DataFrame()

    def get_sector_money_flow(self) -> pd.DataFrame:
        """获取行业板块资金流向排名"""
        try:
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            
            if not df.empty:
                df.rename(columns={
                    '名称': 'sector_name',
                    '今日涨跌幅': 'today_pct_chg',
                    '主力净流入-净额': 'main_net_inflow',
                    '主力净流入-净占比': 'main_net_pct',
                    '超大单净流入-净额': 'super_large_net',
                }, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取行业资金流向失败: {e}")
            return pd.DataFrame()

    # ==================== 5. 股东信息 ====================
    
    def get_shareholder_info(self, ts_code: str) -> pd.DataFrame:
        """获取股东户数和持股变动"""
        symbol = ts_code.split('.')[0]
        
        try:
            df = ak.stock_zh_a_gdhs(symbol=symbol, indicator="总股东")
            
            if not df.empty:
                df['ts_code'] = ts_code
                df.rename(columns={
                    '季度': 'quarter',
                    '股东户数': 'shareholder_count',
                    '较上期变化': 'count_change_pct',
                    '户均持股数': 'avg_shares_per_holder',
                    '户均持股比例': 'avg_hold_pct',
                }, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取 {ts_code} 股东信息失败: {e}")
            return pd.DataFrame()

    # ==================== 6. 龙虎榜数据 ====================
    
    def get_lhb_data(self, date: str = None) -> pd.DataFrame:
        """获取龙虎榜数据（异动股票）"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
            
            if not df.empty:
                df.rename(columns={
                    '代码': 'symbol',
                    '名称': 'name',
                    '上榜原因': 'reason',
                    '买入额': 'buy_amount',
                    '卖出额': 'sell_amount',
                    '净买入额': 'net_amount',
                    '买入机构数': 'buyer_count',
                    '卖出机构数': 'seller_count',
                }, inplace=True)
                
                # 补充ts_code
                df['ts_code'] = df.apply(
                    lambda x: f"{str(x['symbol']).zfill(6)}.SH" if str(x['symbol']).startswith('6') 
                    else f"{str(x['symbol']).zfill(6)}.SZ", axis=1
                )
            
            return df
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {e}")
            return pd.DataFrame()

    # ==================== 7. 数据存储方法 ====================
    
    def save_to_ods(self, table_name: str, df: pd.DataFrame, unique_cols: List[str] = None):
        """
        保存数据到ODS层
        :param table_name: 表名
        :param df: DataFrame数据
        :param unique_cols: 唯一约束列（用于去重）
        """
        if df.empty:
            return
        
        try:
            # 将DataFrame转换为字典列表
            records = df.to_dict('records')
            
            if unique_cols:
                # 使用 INSERT OR IGNORE 去重
                for record in records:
                    placeholders = ', '.join([f':{k}' for k in record.keys()])
                    columns = ', '.join(record.keys())
                    unique_condition = ' AND '.join([f'{col}=:{col}' for col in unique_cols])
                    
                    sql = f"""
                        INSERT OR IGNORE INTO {table_name} ({columns})
                        VALUES ({placeholders})
                        WHERE NOT EXISTS (
                            SELECT 1 FROM {table_name} WHERE {unique_condition}
                        )
                    """.strip().split('WHERE')[0]  # SQLite不支持上述语法，简化处理
                    
                    sql = f"INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders})"
                    
                    self.db.execute(text(sql), record)
            else:
                # 直接插入
                df.to_sql(table_name, self.db.bind, if_exists='append', index=False)
            
            self.db.commit()
            logger.info(f"保存到ODS表 {table_name}: {len(records)} 条记录")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存到ODS失败 {table_name}: {e}")

    # ==================== 8. 全量采集流程 ====================
    
    def collect_all_stocks_full(self, max_stocks: int = 5000, save_to_db: bool = True):
        """
        全量采集所有股票数据（首次使用，约需2-3小时）
        :param max_stocks: 最大采集股票数量
        :param save_to_db: 是否保存到数据库
        """
        start_time = time.time()
        logger.info(f"开始全量采集，目标: {max_stocks} 只股票")
        
        # Step 1: 获取股票列表
        stock_list = self._safe_request(self.get_all_stock_list)
        if stock_list.empty:
            logger.error("无法获取股票列表，终止采集")
            return
        
        codes = stock_list['ts_code'].tolist()[:max_stocks]
        total = len(codes)
        logger.info(f"待采集股票总数: {total}")
        
        if save_to_db:
            self.save_to_ods('ods_stock_basic', stock_list)
        
        # Step 2: 获取行业分类
        logger.info("Step 2: 获取行业分类...")
        industry_map = self.get_stock_industry_classification()
        
        # 保存行业分类
        if industry_map and save_to_db:
            industry_df = pd.DataFrame([
                {'ts_code': k, 'industry_l1': v} for k, v in industry_map.items()
            ])
            self.save_to_ods('ods_stock_industry', industry_df)
        
        # Step 3: 循环采集每只股票的详细数据
        success_count = 0
        fail_count = 0
        
        for i, ts_code in enumerate(codes):
            try:
                logger.info(f"[{i+1}/{total}] 正在采集 {ts_code} ...")
                
                # 3.1 日线行情
                kline_df = self._safe_request(self.get_stock_daily_kline, ts_code, days=365)
                if not kline_df.empty and save_to_db:
                    self.save_to_ods('ods_stock_daily', kline_df, ['ts_code', 'trade_date'])
                
                # 3.2 资金流向（每10只采一次，减少压力）
                if i % 10 == 0:
                    flow_df = self._safe_request(self.get_money_flow_individual, ts_code)
                    if not flow_df.empty and save_to_db:
                        self.save_to_ods('ods_money_flow', flow_df)
                
                # 3.3 财务数据（每20只采一次）
                if i % 20 == 0:
                    fin_df = self._safe_request(self.get_stock_financial, ts_code)
                    if not fin_df.empty and save_to_db:
                        self.save_to_ods('ods_financial', fin_df)
                
                success_count += 1
                
                # 每100只打印进度
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    eta = elapsed / (i + 1) * (total - i - 1) / 60  # 预计剩余时间（分钟）
                    logger.info(f"进度: {i+1}/{total}, 成功: {success_count}, 失败: {fail_count}, 预计剩余: {eta:.1f}分钟")
                
                self._random_delay()
                
            except Exception as e:
                fail_count += 1
                logger.warning(f"[{i+1}/{total}] {ts_code} 采集失败: {e}")
                time.sleep(2)
        
        # Step 4: 采集市场汇总数据
        logger.info("Step 4: 采集市场汇总数据...")
        
        # 北向资金
        north_df = self._safe_request(self.get_north_money_flow)
        if not north_df.empty and save_to_db:
            self.save_to_ods('ods_north_flow', north_df)
        
        # 行业资金流向
        sector_flow_df = self._safe_request(self.get_sector_money_flow)
        if not sector_flow_df.empty and save_to_db:
            self.save_to_ods('ods_sector_flow', sector_flow_df)
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ 全量采集完成!")
        logger.info(f"   总耗时: {elapsed_time/60:.1f} 分钟")
        logger.info(f"   成功: {success_count}, 失败: {fail_count}")
        logger.info(f"   成功率: {success_count/total*100:.1f}%")

    def daily_incremental_update(self, max_stocks: int = 200):
        """
        每日增量更新（建议每天收盘后运行一次）
        只更新最近1天的数据和变化的股票
        """
        logger.info(f"开始每日增量更新...")
        
        # 1. 更新股票列表
        stock_list = self._safe_request(self.get_all_stock_list)
        if not stock_list.empty:
            self.save_to_ods('ods_stock_basic', stock_list)
        
        # 2. 获取昨日涨幅异动的股票（优先更新）
        try:
            # 涨幅前200 + 跌幅前200
            rise_stocks = stock_list.nlargest(200, 'pct_chg')['ts_code'].tolist()
            fall_stocks = stock_list.nsmallest(200, 'pct_chg')['ts_code'].tolist()
            update_codes = list(set(rise_stocks + fall_stocks))[:max_stocks]
        except:
            update_codes = stock_list.head(max_stocks)['ts_code'].tolist()
        
        # 3. 更新这些股票的最新K线
        success = 0
        for ts_code in update_codes:
            try:
                # 只取最近5天
                kline_df = self._safe_request(self.get_stock_daily_kline, ts_code, days=5)
                if not kline_df.empty:
                    self.save_to_ods('ods_stock_daily', kline_df, ['ts_code', 'trade_date'])
                    success += 1
                
                self._random_delay()
            except:
                continue
        
        # 4. 更新市场汇总数据
        north_df = self._safe_request(self.get_north_money_flow)
        if not north_df.empty:
            self.save_to_ods('ods_north_flow', north_df)
        
        sector_flow_df = self._safe_request(self.get_sector_money_flow)
        if not sector_flow_df.empty:
            self.save_to_ods('ods_sector_flow', sector_flow_df)
        
        logger.info(f"✅ 每日增量更新完成! 更新了 {success} 只股票")

    def collect_by_industry(self, target_industries: List[str] = None):
        """
        按行业采集数据（确保各行业都有数据）
        :param target_industries: 目标行业列表，None则采集所有行业
        """
        logger.info("开始按行业采集数据...")
        
        # 获取行业分类
        industry_map = self.get_stock_industry_classification()
        if not industry_map:
            logger.error("无法获取行业分类")
            return
        
        # 按行业分组
        industry_groups = {}
        for ts_code, industry in industry_map.items():
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append(ts_code)
        
        # 过滤目标行业
        if target_industries:
            industry_groups = {k: v for k, v in industry_groups.items() if k in target_industries}
        
        logger.info(f"共 {len(industry_groups)} 个行业待采集")
        
        # 每个行业采集代表性股票（每行业最多50只）
        for industry, stocks in industry_groups.items():
            logger.info(f"\n正在采集行业: {industry} ({len(stocks)} 只)")
            
            sample_stocks = stocks[:min(50, len(stocks))]
            
            for ts_code in sample_stocks:
                try:
                    kline_df = self._safe_request(self.get_stock_daily_kline, ts_code, days=120)
                    if not kline_df.empty:
                        self.save_to_ods('ods_stock_daily', kline_df, ['ts_code', 'trade_date'])
                    
                    self._random_delay()
                except:
                    continue
        
        logger.info(f"✅ 按行业采集完成!")


# ==================== 便捷函数 ====================

def quick_collect_sample(sample_size: int = 100):
    """
    快速采集样本数据（用于测试）
    采集100只代表性股票的数据
    """
    cc = ComprehensiveCollector()
    
    logger.info(f"快速采集模式，样本大小: {sample_size}")
    cc.collect_all_stocks_full(max_stocks=sample_size, save_to_db=True)


def full_collect_all():
    """全量采集所有5000+股票"""
    cc = ComprehensiveCollector()
    cc.collect_all_stocks_full(max_stocks=5500, save_to_db=True)


def daily_update():
    """每日增量更新"""
    cc = ComprehensiveCollector()
    cc.daily_incremental_update(max_stocks=300)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "sample":
            quick_collect_sample(100)
        elif mode == "full":
            full_collect_all()
        elif mode == "update":
            daily_update()
        elif mode == "industry":
            cc = ComprehensiveCollector()
            cc.collect_by_industry()
        else:
            print("用法: python comprehensive_collector.py [sample|full|update|industry]")
    else:
        print("=" * 60)
        print("全面多源数据采集器")
        print("=" * 60)
        print("\n使用方式:")
        print("  python comprehensive_collector.py sample   # 快速采集100只样本")
        print("  python comprehensive_collector.py full     # 全量采集5000+只")
        print("  python comprehensive_collector.py update   # 每日增量更新")
        print("  python comprehensive_collector.py industry # 按行业采集")
        print("\n示例:")
        print("  先测试: python comprehensive_collector.py sample")
        print("  再全量: python comprehensive_collector.py full")
        print("  每日更: python comprehensive_collector.py update")
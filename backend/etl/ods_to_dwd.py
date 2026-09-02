"""
ODS → DWD 层 ETL 脚本
将原始数据清洗后写入明细层
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.database import SessionLocal
from app.utils.logger import logger


def run_ods_to_dwd():
    """执行 ODS → DWD 的 ETL 流程"""
    db: Session = SessionLocal()
    try:
        logger.info("开始执行 ODS → DWD ETL...")

        # 日线行情 ODS → DWD
        _ods_to_dwd_daily(db)

        # 股票信息 ODS → DWD
        _ods_to_dwd_stock_info(db)

        # 财务数据 ODS → DWD
        _ods_to_dwd_financial(db)

        db.commit()
        logger.info("ODS → DWD ETL 完成")
    except Exception as e:
        db.rollback()
        logger.error(f"ODS → DWD ETL 异常: {e}")
        raise
    finally:
        db.close()


def _ods_to_dwd_daily(db: Session):
    """日线行情 ODS → DWD"""
    sql = text("""
        INSERT INTO dwd_stock_daily 
            (ts_code, trade_date, open, high, low, close, pre_close, 
             `change`, pct_chg, vol, amount, turn, amplitude, is_st, data_quality)
        SELECT 
            ts_code,
            trade_date,
            open,
            high,
            low,
            close,
            pre_close,
            COALESCE(`change`, close - pre_close) as `change`,
            COALESCE(pct_chg, (close - pre_close) / pre_close * 100) as pct_chg,
            vol,
            amount,
            turn,
            CASE 
                WHEN high > 0 AND low > 0 AND pre_close > 0 
                THEN ROUND((high - low) / pre_close * 100, 3) 
                ELSE 0 
            END as amplitude,
            CASE WHEN ts_code LIKE '%ST%' THEN 1 ELSE 0 END as is_st,
            CASE WHEN close > 0 AND open > 0 AND high >= low THEN 1 ELSE 0 END as data_quality
        FROM ods_stock_daily
        WHERE (ts_code, trade_date) NOT IN (SELECT ts_code, trade_date FROM dwd_stock_daily)
          AND close > 0
    """)
    result = db.execute(sql)
    logger.info(f"日线行情 ODS→DWD: {result.rowcount} 行")


def _ods_to_dwd_stock_info(db: Session):
    """股票信息 ODS → DWD（按名称关键词精确匹配行业分类）"""
    sql = text("""
        INSERT INTO dwd_stock_info 
            (ts_code, symbol, name, area, industry_l1, market, list_date, is_st)
        SELECT 
            ts_code,
            symbol,
            name,
            area,
            CASE 
                -- 金融类
                WHEN name LIKE '%银行%' OR name LIKE '%保险%' OR name LIKE '%证券%' 
                     OR name LIKE '%信托%' OR name LIKE '%租赁%' OR name LIKE '%期货%'
                     OR name LIKE '%金融%' OR name LIKE '%投资%' OR name LIKE '%典当%' THEN '金融地产'
                -- 房地产建筑
                WHEN name LIKE '%地产%' OR name LIKE '%房产%' OR name LIKE '%物业%' 
                     OR name LIKE '%建筑%' OR name LIKE '%建材%' OR name LIKE '%装饰%'
                     OR name LIKE '%家居%' OR name LIKE '%园林%' OR name LIKE '%装修%'
                     OR name LIKE '%设计%' THEN '房地产建筑'
                -- 医药生物
                WHEN name LIKE '%医药%' OR name LIKE '%生物%' OR name LIKE '%医疗%' 
                     OR name LIKE '%制药%' OR name LIKE '%药业%' OR name LIKE '%健康%'
                     OR name LIKE '%疫苗%' OR name LIKE '%基因%' OR name LIKE '%器械%'
                     OR name LIKE '%试剂%' OR name LIKE '%药房%' OR name LIKE '%中药%'
                     OR name LIKE '%化学药%' THEN '消费医药'
                -- 半导体电子
                WHEN name LIKE '%电子%' OR name LIKE '%芯片%' OR name LIKE '%半导体%' 
                     OR name LIKE '%集成电路%' OR name LIKE '%PCB%' OR name LIKE '%显示%'
                     OR name LIKE '%光电%' OR name LIKE '%光学%' OR name LIKE '%传感器%'
                     OR name LIKE '%激光%' OR name LIKE '%红外%' OR name LIKE '%镜头%' THEN '半导体电子'
                -- 信息技术/软件
                WHEN name LIKE '%软件%' OR name LIKE '%信息%' OR name LIKE '%网络%' 
                     OR name LIKE '%通信%' OR name LIKE '%互联网%' OR name LIKE '%数据%' 
                     OR name LIKE '%云计算%' OR name LIKE '%AI%' OR name LIKE '%智能%'
                     OR name LIKE '%科技%' OR name LIKE '%数字%' OR name LIKE '%电商%'
                     OR name LIKE '%支付%' OR name LIKE '%安全%' OR name LIKE '%物联网%' THEN '信息技术'
                -- 新能源材料
                WHEN name LIKE '%电力%' OR name LIKE '%能源%' OR name LIKE '%光伏%' 
                     OR name LIKE '%锂电%' OR name LIKE '%风电%' OR name LIKE '%核电%' 
                     OR name LIKE '%电池%' OR name LIKE '%新能源%' OR name LIKE '%储能%'
                     OR name LIKE '%充电%' OR name LIKE '%太阳能%' OR name LIKE '%氢能%'
                     OR name LIKE '%节能%' OR name LIKE '%环保%' OR name LIKE '%电网%'
                     OR name LIKE '%电气%' OR name LIKE '%电材%' THEN '新能源材料'
                -- 新能源汽车
                WHEN name LIKE '%汽车%' OR name LIKE '%汽配%' OR name LIKE '%新能源车%'
                     OR name LIKE '%轮胎%' THEN '新能源汽车'
                -- 大消费
                WHEN name LIKE '%食品%' OR name LIKE '%饮料%' OR name LIKE '%酒%' 
                     OR name LIKE '%餐饮%' OR name LIKE '%家电%' OR name LIKE '%零售%'
                     OR name LIKE '%百货%' OR name LIKE '%超市%' OR name LIKE '%服装%'
                     OR name LIKE '%纺织%' OR name LIKE '%服饰%' OR name LIKE '%化妆%'
                     OR name LIKE '%美容%' OR name LIKE '%乳%' OR name LIKE '%旅游%'
                     OR name LIKE '%酒店%' OR name LIKE '%免税%' OR name LIKE '%宠物%' THEN '大消费'
                -- 基础化工
                WHEN name LIKE '%化工%' OR name LIKE '%石化%' OR name LIKE '%化学%' 
                     OR name LIKE '%塑料%' OR name LIKE '%橡胶%' OR name LIKE '%化肥%'
                     OR name LIKE '%农药%' OR name LIKE '%涂料%' OR name LIKE '%树脂%'
                     OR name LIKE '%纤维%' OR name LIKE '%胶%' THEN '基础化工'
                -- 有色金属/钢铁/煤炭
                WHEN name LIKE '%钢铁%' OR name LIKE '%有色%' OR name LIKE '%金属%' 
                     OR name LIKE '%矿产%' OR name LIKE '%煤炭%' OR name LIKE '%黄金%'
                     OR name LIKE '%铜%' OR name LIKE '%铝%' OR name LIKE '%锌%'
                     OR name LIKE '%稀土%' OR name LIKE '%合金%' OR name LIKE '%矿%' THEN '有色金属'
                -- 工业制造
                WHEN name LIKE '%机械%' OR name LIKE '%设备%' OR name LIKE '%重工%' 
                     OR name LIKE '%装备%' OR name LIKE '%军工%' OR name LIKE '%航天%'
                     OR name LIKE '%航空%' OR name LIKE '%船舶%' OR name LIKE '%仪器%'
                     OR name LIKE '%仪表%' OR name LIKE '%自动化%' OR name LIKE '%机器人%'
                     OR name LIKE '%电器%' OR name LIKE '%电机%' OR name LIKE '%电梯%'
                     OR name LIKE '%轴承%' OR name LIKE '%模具%' OR name LIKE '%机床%' THEN '工业制造'
                -- 交通运输
                WHEN name LIKE '%运输%' OR name LIKE '%物流%' OR name LIKE '%航空%' 
                     OR name LIKE '%港口%' OR name LIKE '%航运%' OR name LIKE '%铁路%'
                     OR name LIKE '%公路%' OR name LIKE '%高速%' OR name LIKE '%机场%'
                     OR name LIKE '%快递%' OR name LIKE '%海运%' OR name LIKE '%交通%' THEN '交通运输'
                -- 文化传媒
                WHEN name LIKE '%传媒%' OR name LIKE '%文化%' OR name LIKE '%教育%' 
                     OR name LIKE '%游戏%' OR name LIKE '%影视%' OR name LIKE '%出版%'
                     OR name LIKE '%广告%' OR name LIKE '%娱乐%' OR name LIKE '%体育%'
                     OR name LIKE '%广电%' THEN '文化传媒'
                -- 农林牧渔
                WHEN name LIKE '%农业%' OR name LIKE '%林业%' OR name LIKE '%牧业%' 
                     OR name LIKE '%渔业%' OR name LIKE '%种业%' OR name LIKE '%养殖%'
                     OR name LIKE '%种植%' OR name LIKE '%饲料%' OR name LIKE '%兽药%'
                     OR name LIKE '%水产%' OR name LIKE '%畜牧%' OR name LIKE '%农机%' THEN '农林牧渔'
                
                -- 代码段粗略匹配（仅用于无法通过名称判断的）
                WHEN ts_code LIKE '601%' THEN '金融地产'
                WHEN ts_code LIKE '000%' THEN '综合企业'
                WHEN ts_code LIKE '002%' THEN '中小板龙头'
                WHEN ts_code LIKE '300%' THEN '信息技术'
                WHEN ts_code LIKE '688%' THEN '半导体电子'
                WHEN ts_code LIKE '600%' THEN '工业制造'
                WHEN ts_code LIKE '603%' THEN '工业制造'
                WHEN ts_code LIKE '605%' THEN '工业制造'
                
                ELSE '其他'
            END as industry_l1,
            market,
            list_date,
            CASE WHEN name LIKE '%ST%' OR name LIKE '%*ST%' THEN 1 ELSE 0 END as is_st
        FROM ods_stock_basic
        WHERE ts_code NOT IN (SELECT ts_code FROM dwd_stock_info)
    """)
    result = db.execute(sql)
    logger.info(f"股票信息 ODS→DWD: {result.rowcount} 行")


def _ods_to_dwd_financial(db: Session):
    """财务数据 ODS → DWD"""
    sql = text("""
        INSERT INTO dwd_financial_indicator 
            (ts_code, end_date, report_type, revenue, n_income, eps, total_assets, total_hldr_eqy)
        SELECT 
            i.ts_code,
            i.end_date,
            i.report_type,
            COALESCE(i.revenue, 0),
            COALESCE(i.n_income, 0),
            COALESCE(i.eps, 0),
            COALESCE(b.total_assets, 0),
            COALESCE(b.total_hldr_eqy, 0)
        FROM ods_income i
        LEFT JOIN ods_balancesheet b 
            ON i.ts_code = b.ts_code 
            AND i.end_date = b.end_date 
            AND i.report_type = b.report_type
        WHERE (i.ts_code, i.end_date, i.report_type) 
            NOT IN (SELECT ts_code, end_date, report_type FROM dwd_financial_indicator)
    """)
    result = db.execute(sql)
    logger.info(f"财务指标 ODS→DWD: {result.rowcount} 行")
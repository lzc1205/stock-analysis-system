"""
修复行业分类 - 使用更全面的名称关键词匹配
覆盖5000+只股票，不再依赖宽泛的代码段匹配
"""
from app.utils.database import SessionLocal
from sqlalchemy import text
from app.utils.logger import logger


def get_industry_by_name(name: str, ts_code: str) -> str:
    """
    根据股票名称和代码判断行业分类
    使用更全面的关键词匹配，覆盖各行各业
    """
    # 金融类
    if any(kw in name for kw in ['银行', '保险', '证券', '信托', '租赁', '期货', '金融', '投资', '典当']):
        return '金融地产'
    
    # 房地产建筑
    if any(kw in name for kw in ['地产', '房产', '物业', '建筑', '建材', '装饰', '家居', '园林', '装修', '设计']):
        return '房地产建筑'
    
    # 医药生物
    if any(kw in name for kw in ['医药', '生物', '医疗', '制药', '药业', '健康', '疫苗', '基因', '干细胞', '抗癌', '器械', '试剂', '药房', '中药', '化学药']):
        return '消费医药'
    
    # 半导体电子
    if any(kw in name for kw in ['电子', '芯片', '半导体', '集成电路', 'PCB', '显示', '光电', '光学', '传感器', '激光', '红外', '镜头']):
        return '半导体电子'
    
    # 信息技术/软件
    if any(kw in name for kw in ['软件', '信息', '网络', '通信', '互联网', '数据', '云计算', '智能', 'AI', '科技', '数字', '互联', '电商', '支付', '安全', '物联网', '区块链', '算力', '大数据', '量子']):
        return '信息技术'
    
    # 新能源材料
    if any(kw in name for kw in ['电力', '能源', '光伏', '锂电', '风电', '核电', '电池', '新能源', '储能', '充电', '太阳能', '氢能', '节能', '环保', '碳', '清洁', '再生', '电网', '电气', '电材']):
        return '新能源材料'
    
    # 新能源汽车
    if any(kw in name for kw in ['汽车', '汽配', '新能源车', '自动驾驶', '轮胎', '车', '驾驶']):
        return '新能源汽车'
    
    # 大消费
    if any(kw in name for kw in ['食品', '饮料', '酒', '餐饮', '家电', '零售', '百货', '超市', '服装', '纺织', '服饰', '家纺', '鞋', '帽', '化妆', '美容', '乳', '奶', '肉', '粮', '米', '油', '调味', '零食', '糖果', '烟草', '旅游', '酒店', '免税', '宠物', '日化', '卫生']):
        return '大消费'
    
    # 基础化工
    if any(kw in name for kw in ['化工', '石化', '化学', '塑料', '橡胶', '化肥', '农药', '涂料', '染料', '颜料', '树脂', '纤维', '聚酯', '聚氨', '硅胶', '膜', '胶', '钾', '磷', '氟', '氯', '碱', '钛', '氨', '甲醇', '乙']):
        return '基础化工'
    
    # 有色金属/钢铁/煤炭
    if any(kw in name for kw in ['钢铁', '有色', '金属', '矿产', '煤炭', '黄金', '银', '铜', '铝', '锌', '锡', '镍', '钴', '锂', '稀土', '钨', '钼', '铁', '矿', '焦煤', '金矿', '合金', '特钢', '板材', '管材']):
        return '有色金属'
    
    # 工业制造
    if any(kw in name for kw in ['机械', '设备', '重工', '装备', '军工', '航天', '航空', '船舶', '仪器', '仪表', '检测', '自动化', '机器人', '电器', '开关', '电机', '电梯', '变压器', '泵', '阀', '密封', '轴承', '模具', '工具', '铸造', '锻造', '焊接', '机床', '液压', '齿轮']):
        return '工业制造'
    
    # 交通运输
    if any(kw in name for kw in ['运输', '物流', '航空', '港口', '航运', '铁路', '公路', '高速', '机场', '快递', '海运', '船舶运输', '地铁', '轨道', '交通', '客车', '货车', '出租车', '民航']):
        return '交通运输'
    
    # 文化传媒
    if any(kw in name for kw in ['传媒', '文化', '教育', '游戏', '影视', '出版', '广告', '娱乐', '体育', '动漫', '音乐', '视频', '直播', '教育', '培训', '报纸', '杂志', '广电', '版权', 'IP']):
        return '文化传媒'
    
    # 农林牧渔
    if any(kw in name for kw in ['农业', '林业', '牧业', '渔业', '种业', '养殖', '种植', '饲料', '兽药', '水产', '畜牧', '农化', '农机', '米业', '林业', '种子', '棉花', '橡胶种植', '糖', '甘蔗']):
        return '农林牧渔'
    
    # 环保
    if any(kw in name for kw in ['环保', '环境', '水务', '垃圾', '环卫', '污水处理', '固废', '大气', '检测']):
        return '新能源材料'
    
    # 代码段精细匹配（仅用于无法通过名称判断的）
    # 银行股（600000-600016, 601xxx）
    if ts_code in ['600000.SH', '600015.SH', '600016.SH', '600036.SH', '600919.SH', '600926.SH', '601009.SH', 
                   '601128.SH', '601166.SH', '601169.SH', '601187.SH', '601229.SH', '601288.SH', '601328.SH',
                   '601398.SH', '601528.SH', '601577.SH', '601818.SH', '601838.SH', '601860.SH', '601916.SH',
                   '601939.SH', '601963.SH', '601988.SH', '601997.SH', '601998.SH']:
        return '金融地产'
    
    # 券商（600xxx + 601xxx + 002xxx）
    if any(kw in name for kw in ['证券', '券商', '期货', '信托']):
        return '金融地产'
    
    # 保险
    if any(kw in name for kw in ['保险', '人寿', '平安', '太保', '人保']):
        return '金融地产'
    
    # 默认按代码段粗略分类
    if ts_code.startswith('688') or ts_code.startswith('689'):
        return '半导体电子'
    if ts_code.startswith('300'):
        return '信息技术'
    if ts_code.startswith('301'):
        return '信息技术'
    if ts_code.startswith('002'):
        return '中小板龙头'
    if ts_code.startswith('000'):
        return '综合企业'
    if ts_code.startswith('600'):
        return '工业制造'  # 600xxx not matched above → generic industrial
    if ts_code.startswith('601'):
        return '金融地产'  # 601xxx mostly financial
    if ts_code.startswith('603'):
        return '工业制造'
    if ts_code.startswith('605'):
        return '工业制造'
    
    return '其他'


def fix_industry_classification():
    """修复所有股票的行业分类"""
    db = SessionLocal()
    
    try:
        # 获取所有股票信息
        result = db.execute(text("SELECT ts_code, name FROM dwd_stock_info")).fetchall()
        total = len(result)
        logger.info(f"开始修复 {total} 只股票的行业分类...")
        
        updated = 0
        stats = {}
        
        for row in result:
            ts_code = row[0]
            name = row[1]
            
            new_industry = get_industry_by_name(name, ts_code)
            
            # 统计
            stats[new_industry] = stats.get(new_industry, 0) + 1
            
            # 更新
            db.execute(
                text("UPDATE dwd_stock_info SET industry_l1 = :industry WHERE ts_code = :ts_code"),
                {"industry": new_industry, "ts_code": ts_code}
            )
            updated += 1
        
        db.commit()
        
        logger.info(f"修复完成! 更新了 {updated} 只股票")
        logger.info("\n行业分布:")
        for ind, cnt in sorted(stats.items(), key=lambda x: -x[1]):
            logger.info(f"  {ind}: {cnt}")
        
        return stats
        
    except Exception as e:
        db.rollback()
        logger.error(f"修复行业分类失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_industry_classification()
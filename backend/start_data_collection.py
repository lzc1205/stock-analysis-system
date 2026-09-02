"""
数据采集快速启动脚本
一键启动全面数据采集，覆盖5000+个股和各行各业
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collector.comprehensive_collector import (
    ComprehensiveCollector,
    quick_collect_sample,
    full_collect_all,
    daily_update
)
from app.utils.logger import logger


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          📊 A股全市场数据采集系统 v2.0                       ║
║                                                              ║
║     覆盖 5000+ 个股 | 109个行业 | 多源数据整合              ║
║                                                              ║
║     数据源: AkShare + 东方财富 + 新浪财经                    ║
║     数据类型: 行情/财务/资金流向/股东/龙虎榜                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def show_menu():
    """显示菜单"""
    menu = """
请选择采集模式:

  [1] 🚀 快速测试 (100只股票, 约5分钟)
      → 验证系统是否正常工作
      → 获取各行业代表性股票数据
      
  [2] ⭐ 标准采集 (500只股票, 约30分钟)
      → 覆盖主要行业龙头股
      → 包含完整行情和资金数据
      
  [3] 🔥 全量采集 (5000+只股票, 2-3小时)
      → 覆盖全市场所有A股
      → 最完整的数据集
      
  [4] 📅 每日增量更新 (异动股票, 约10分钟)
      → 每天收盘后运行一次
      → 更新最新行情和资金流向
      
  [5] 🏭 按行业采集 (确保各行业覆盖)
      → 重点采集特定行业
      → 保证数据均衡性
  
  [0] ❌ 退出

请输入选项编号: """
    
    return input(menu).strip()


def run_quick_test():
    """运行快速测试"""
    print("\n" + "="*60)
    print("🚀 模式: 快速测试 (100只股票)")
    print("="*60)
    print("\n正在采集100只代表性股票的数据...")
    print("包含: 各行业龙头 + 高流动性股票\n")
    
    quick_collect_sample(sample_size=100)
    
    print("\n✅ 快速测试完成!")
    print("\n下一步:")
    print("  - 运行 ETL: python -c \"from etl.ods_to_dwd import run_ods_to_dwd; run_ods_to_dwd()\"")
    print("  - 启动前端: cd frontend && npm run dev")
    print("  - 或继续全量采集: 选择选项 [3]")


def run_standard_collection():
    """标准采集"""
    print("\n" + "="*60)
    print("⭐ 模式: 标准采集 (500只股票)")
    print("="*60)
    print("\n正在采集500只主要股票...")
    print("包含: 各行业前50名 + 主要指数成分股\n")
    
    cc = ComprehensiveCollector()
    cc.collect_all_stocks_full(max_stocks=500, save_to_db=True)
    
    print("\n✅ 标准采集完成!")


def run_full_collection():
    """全量采集"""
    print("\n" + "="*60)
    print("🔥 模式: 全量采集 (5000+只股票)")
    print("="*60)
    
    confirm = input("\n⚠️  全量采集需要 2-3 小时，确定继续吗? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    print("\n正在采集全市场5000+只股票数据...")
    print("包含: 所有A股完整数据\n")
    
    cc = ComprehensiveCollector()
    cc.collect_all_stocks_full(max_stocks=5500, save_to_db=True)
    
    print("\n✅ 全量采集完成! 现在拥有最完整的A股数据库")


def run_daily_update():
    """每日更新"""
    print("\n" + "="*60)
    print("📅 模式: 每日增量更新")
    print("="*60)
    print("\n正在更新今日异动股票数据...\n")
    
    daily_update()
    
    print("\n✅ 每日更新完成!")
    print("建议: 设置定时任务，每天收盘后自动运行")


def run_industry_collection():
    """按行业采集"""
    print("\n" + "="*60)
    print("🏭 模式: 按行业采集")
    print("="*60)
    
    print("\n可选行业 (输入编号，多个用逗号分隔):")
    print("  [1] 全部行业")
    print("  [2] 金融地产 (银行/保险/证券)")
    print("  [3] 消费医药 (医药/食品/家电)")
    print("  [4] 科技 (半导体/软件/电子)")
    print("  [5] 新能源 (光伏/锂电/风电)")
    print("  [6] 制造 (汽车/机械/军工)")
    print("  [7] 周期 (化工/钢铁/有色)")
    print("  [8] 其他 (自定义)")
    
    choice = input("\n请选择: ").strip()
    
    target_industries = None
    
    if choice == '1':
        target_industries = None  # 全部
    elif choice == '2':
        target_industries = ['银行', '保险', '证券', '信托']
    elif choice == '3':
        target_industries = ['医药', '生物制品', '食品饮料', '家用电器', '商业零售']
    elif choice == '4':
        target_industries = ['半导体', '软件开发', '电子元件', '通信设备', '互联网']
    elif choice == '5':
        target_industries = ['光伏', '电池', '风电', '新能源']
    elif choice == '6':
        target_industries = ['汽车', '机械设备', '国防军工']
    elif choice == '7':
        target_industries = ['化学原料', '钢铁', '有色金属', '煤炭']
    elif choice == '8':
        custom = input("请输入行业名称 (多个用逗号分隔): ").strip()
        target_industries = [ind.strip() for ind in custom.split(',')]
    else:
        print("无效选择")
        return
    
    print(f"\n目标行业: {target_industries or '全部'}")
    print("开始采集...\n")
    
    cc = ComprehensiveCollector()
    cc.collect_by_industry(target_industries=target_industries)
    
    print("\n✅ 按行业采集完成!")


def main():
    """主函数"""
    print_banner()
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_quick_test()
        elif choice == '2':
            run_standard_collection()
        elif choice == '3':
            run_full_collection()
        elif choice == '4':
            run_daily_update()
        elif choice == '5':
            run_industry_collection()
        elif choice == '0':
            print("\n感谢使用! 再见 👋\n")
            break
        else:
            print("\n❌ 无效选项，请重新选择!\n")
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出程序")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        print(f"\n❌ 程序异常: {e}")
        print("请检查日志文件获取详细信息")
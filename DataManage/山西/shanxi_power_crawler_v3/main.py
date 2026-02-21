"""
主程序入口 - 交互式版本
"""

import json
import os
from crawler.node_price_crawler import NodePriceCrawler
from utils.logger import logger
from utils.date_utils import get_current_date, get_month_range, get_recent_days
from datetime import datetime
from config.settings import NODES_CONFIG_FILE


def print_menu():
    """打印菜单"""
    print("\n" + "=" * 70)
    print("        山西电力交易中心 - 日前节点边际电价爬虫 v3.0")
    print("=" * 70)
    print("1. 爬取单日单节点数据")
    print("2. 爬取日期范围单节点数据")
    print("3. 爬取最近 N 天数据")
    print("4. 爬取当前月份数据")
    print("5. 查看常用节点列表")
    print("6. 测试 Cookie 是否有效")
    print("0. 退出程序")
    print("=" * 70)


def load_nodes_config():
    """加载节点配置"""
    try:
        if os.path.exists(NODES_CONFIG_FILE):
            with open(NODES_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载节点配置失败: {str(e)}")
    return {}


def show_common_nodes():
    """显示常用节点"""
    config = load_nodes_config()

    print("\n" + "=" * 70)
    print("📍 常用节点列表")
    print("=" * 70)

    # 显示常用节点
    common_nodes = config.get('常用节点', [])
    if common_nodes:
        print("\n【常用节点】")
        for i, node in enumerate(common_nodes, 1):
            print(f"  {i}. {node}")

    # 显示节点分类
    categories = config.get('节点分类', {})
    if categories:
        print("\n【节点分类】")
        for category, nodes in categories.items():
            print(f"\n  {category}:")
            for node in nodes[:5]:  # 只显示前5个
                print(f"    - {node}")
            if len(nodes) > 5:
                print(f"    ... (共 {len(nodes)} 个节点)")

    print("\n" + "=" * 70)


def get_user_input(prompt: str, default: str = None) -> str:
    """获取用户输入"""
    if default:
        user_input = input(f"{prompt} [默认: {default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()


def validate_date(date_str: str) -> bool:
    """验证日期格式"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def input_cookie() -> str:
    """输入Cookie"""
    print("\n" + "=" * 70)
    print("请输入Cookie（支持两种格式）：")
    print("1. 浏览器复制的Cookie字符串")
    print("2. EditThisCookie导出的JSON格式")
    print("\n输入完成后，单独一行输入 END 结束")
    print("=" * 70)

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    cookies_input = '\n'.join(lines).strip()

    if not cookies_input:
        print("❌ Cookie不能为空")
        return None

    return cookies_input


def option_1_single_day(crawler: NodePriceCrawler):
    """选项1: 爬取单日单节点"""
    print("\n" + "=" * 70)
    print("📌 爬取单日单节点数据")
    print("=" * 70)

    node_name = get_user_input("请输入节点名称（例如：华北.太钢/500kV.1母线）")
    if not node_name:
        print("❌ 节点名称不能为空")
        return

    date_str = get_user_input("请输入日期 (YYYY-MM-DD)", get_current_date())
    if not validate_date(date_str):
        print("❌ 日期格式错误")
        return

    save_format = get_user_input("保存格式 (excel/csv/json)", "excel")

    print(f"\n将爬取: {node_name} - {date_str}")
    confirm = get_user_input("确认开始爬取? (y/n)", "y")
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return

    crawler.crawl_and_save(node_name, date_str, date_str, save_format)


def option_2_date_range(crawler: NodePriceCrawler):
    """选项2: 爬取日期范围"""
    print("\n" + "=" * 70)
    print("📌 爬取日期范围单节点数据")
    print("=" * 70)

    node_name = get_user_input("请输入节点名称（例如：华北.太钢/500kV.1母线）")
    if not node_name:
        print("❌ 节点名称不能为空")
        return

    while True:
        start_date = get_user_input("请输入开始日期 (YYYY-MM-DD)", get_current_date())
        if validate_date(start_date):
            break
        print("❌ 日期格式错误")

    while True:
        end_date = get_user_input("请输入结束日期 (YYYY-MM-DD)", get_current_date())
        if validate_date(end_date):
            break
        print("❌ 日期格式错误")

    if start_date > end_date:
        print("❌ 开始日期不能大于结束日期")
        return

    save_format = get_user_input("保存格式 (excel/csv/json)", "excel")

    print(f"\n将爬取: {node_name}")
    print(f"日期范围: {start_date} 至 {end_date}")
    confirm = get_user_input("确认开始爬取? (y/n)", "y")
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return

    crawler.crawl_and_save(node_name, start_date, end_date, save_format)


def option_3_recent_days(crawler: NodePriceCrawler):
    """选项3: 爬取最近N天"""
    print("\n" + "=" * 70)
    print("📌 爬取最近 N 天数据")
    print("=" * 70)

    node_name = get_user_input("请输入节点名称（例如：华北.太钢/500kV.1母线）")
    if not node_name:
        print("❌ 节点名称不能为空")
        return

    while True:
        try:
            days = int(get_user_input("请输入天数", "7"))
            if days > 0:
                break
            print("❌ 天数必须大于0")
        except ValueError:
            print("❌ 请输入有效的数字")

    start_date, end_date = get_recent_days(days)
    save_format = get_user_input("保存格式 (excel/csv/json)", "excel")

    print(f"\n将爬取: {node_name}")
    print(f"最近 {days} 天: {start_date} 至 {end_date}")
    confirm = get_user_input("确认开始爬取? (y/n)", "y")
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return

    crawler.crawl_and_save(node_name, start_date, end_date, save_format)


def option_4_current_month(crawler: NodePriceCrawler):
    """选项4: 爬取当前月份"""
    print("\n" + "=" * 70)
    print("📌 爬取当前月份数据")
    print("=" * 70)

    node_name = get_user_input("请输入节点名称（例如：华北.太钢/500kV.1母线）")
    if not node_name:
        print("❌ 节点名称不能为空")
        return

    start_date, end_date = get_month_range()
    save_format = get_user_input("保存格式 (excel/csv/json)", "excel")

    print(f"\n将爬取: {node_name}")
    print(f"当前月份: {start_date} 至 {end_date}")
    confirm = get_user_input("确认开始爬取? (y/n)", "y")
    if confirm.lower() != 'y':
        print("❌ 已取消")
        return

    crawler.crawl_and_save(node_name, start_date, end_date, save_format)


def option_5_show_nodes():
    """选项5: 查看节点列表"""
    show_common_nodes()


def option_6_test_cookie(crawler: NodePriceCrawler):
    """选项6: 测试Cookie"""
    print("\n" + "=" * 70)
    print("🔍 测试 Cookie 是否有效")
    print("=" * 70)

    crawler.test_connection()


def main():
    """主函数"""
    try:
        logger.info("程序启动")

        # 输入Cookie
        cookies = input_cookie()
        if not cookies:
            return

        # 创建爬虫实例
        crawler = NodePriceCrawler(cookies)

        while True:
            print_menu()
            choice = get_user_input("请选择功能")

            if choice == '1':
                option_1_single_day(crawler)
            elif choice == '2':
                option_2_date_range(crawler)
            elif choice == '3':
                option_3_recent_days(crawler)
            elif choice == '4':
                option_4_current_month(crawler)
            elif choice == '5':
                option_5_show_nodes()
            elif choice == '6':
                option_6_test_cookie(crawler)
            elif choice == '0':
                print("\n👋 感谢使用，再见！")
                break
            else:
                print("\n❌ 无效的选择，请重新输入")

            # 询问是否继续
            if choice in ['1', '2', '3', '4', '6']:
                print("\n" + "-" * 70)
                continue_choice = get_user_input("是否继续使用? (y/n)", "y")
                if continue_choice.lower() != 'y':
                    print("\n👋 感谢使用，再见！")
                    break

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序")
        logger.warning("用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序执行失败: {str(e)}")
        logger.error(f"程序执行失败: {str(e)}", exc_info=True)
    finally:
        logger.info("程序退出")


if __name__ == "__main__":
    main()

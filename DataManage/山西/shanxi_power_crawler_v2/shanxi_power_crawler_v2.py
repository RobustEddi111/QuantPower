# shanxi_power_crawler_v2.py
"""
山西电力交易中心爬虫 - 增强版
支持配置文件和交互输入两种方式
"""

from input_manager import InputManager
from ShanxiPowerPriceCrawler import ShanxiPowerPriceCrawler
from config import *


def main():
    print("=" * 70)
    print("🔌 山西电力交易中心 - 节点电价数据爬虫 (增强版)")
    print("=" * 70)

    # 1. 获取Cookie
    cookies = InputManager.get_cookies()
    if not cookies:
        print("❌ Cookie不能为空")
        return

    # 2. 创建爬虫实例
    crawler = ShanxiPowerPriceCrawler(cookies)

    # 3. 获取运行模式
    mode = InputManager.get_run_mode()

    # 4. 根据模式执行
    if mode == 1:
        # 单日爬取
        node_name = input("请输入节点名称: ").strip()
        date_str = input("请输入日期 (YYYY-MM-DD): ").strip()

        data = crawler.fetch_price_data(node_name, date_str)
        if data:
            crawler.save_to_csv(data, f"{node_name}_{date_str}.csv")

    elif mode == 2:
        # 日期范围爬取
        node_name = input("请输入节点名称: ").strip()
        start_date, end_date = InputManager.get_date_range()

        all_data = crawler.crawl_date_range(node_name, start_date, end_date)
        if all_data:
            crawler.save_to_csv(all_data, f"{node_name}_{start_date}_to_{end_date}.csv")

    elif mode == 3:
        # 批量节点爬取
        nodes = InputManager.get_nodes()
        start_date, end_date = InputManager.get_date_range()

        crawler.batch_fetch_nodes(nodes, start_date, end_date)

    print("\n✅ 任务完成！")


if __name__ == "__main__":
    main()

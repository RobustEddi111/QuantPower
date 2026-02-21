"""
节点电价爬虫
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.settings import NODE_PRICE_API, PAGE_SIZE
from utils.logger import logger
from utils.date_utils import get_date_range, parse_date, format_date
from utils.file_handler import FileHandler
from .base_crawler import BaseCrawler


class NodePriceCrawler(BaseCrawler):
    """节点电价爬虫类"""

    def __init__(self, cookies: str = None):
        """
        初始化节点电价爬虫

        Args:
            cookies: Cookie字符串或JSON格式
        """
        super().__init__(cookies)
        self.api_url = self.base_url + NODE_PRICE_API
        logger.info("节点电价爬虫初始化完成")

    def fetch_single_day(self, node_name: str, date_str: str) -> Optional[List[Dict]]:
        """
        获取单日单节点的电价数据

        Args:
            node_name: 节点名称
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            List[Dict]: 数据列表，失败返回None
        """
        payload = {
            "data": {
                "nodeName": node_name,
                "atDate": date_str
            },
            "pageInfo": {
                "pageNum": 1,
                "pageSize": PAGE_SIZE
            }
        }

        try:
            logger.debug(f"正在获取: {date_str} {node_name}")

            response_data = self.post(self.api_url, json=payload)

            if not response_data:
                logger.error(f"❌ {date_str} {node_name}: 请求失败")
                return None

            # 检查响应状态
            if not self._check_response(response_data):
                return None

            # 提取数据
            data_list = response_data.get('data', {}).get('list', [])

            if data_list:
                logger.info(f"✅ {date_str} {node_name}: 获取 {len(data_list)} 条数据")
            else:
                logger.warning(f"⚠️ {date_str} {node_name}: 无数据")

            return data_list

        except Exception as e:
            logger.error(f"❌ {date_str} {node_name}: 异常 - {str(e)}", exc_info=True)
            return None

    def fetch_date_range(self, node_name: str, start_date: str, end_date: str) -> List[Dict]:
        """
        获取日期范围内的数据

        Args:
            node_name: 节点名称
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            List[Dict]: 所有数据列表
        """
        logger.info("=" * 70)
        logger.info(f"📅 爬取日期范围: {start_date} 至 {end_date}")
        logger.info(f"📍 节点名称: {node_name}")
        logger.info("=" * 70)

        all_data = []
        date_list = get_date_range(start_date, end_date)
        total_dates = len(date_list)

        for index, date_str in enumerate(date_list, 1):
            logger.info(f"进度: {index}/{total_dates}")

            data = self.fetch_single_day(node_name, date_str)

            if data is None:
                # Cookie失效，停止爬取
                logger.error("❌ Cookie已失效，停止爬取")
                break

            if data:
                all_data.extend(data)

            # 延迟，避免请求过快
            if index < total_dates:
                self.sleep()

        logger.info("=" * 70)
        logger.info(f"✅ 爬取完成！共获取 {len(all_data)} 条数据")
        logger.info("=" * 70)

        return all_data

    def crawl_and_save(self, node_name: str, start_date: str = None,
                       end_date: str = None, save_format: str = 'excel') -> Optional[str]:
        """
        爬取数据并保存

        Args:
            node_name: 节点名称
            start_date: 开始日期，默认今天
            end_date: 结束日期，默认今天
            save_format: 保存格式 ('excel', 'csv', 'json')

        Returns:
            str: 保存的文件路径
        """
        from utils.date_utils import get_current_date

        # 默认日期为今天
        if not start_date:
            start_date = get_current_date()
        if not end_date:
            end_date = start_date

        # 爬取数据
        if start_date == end_date:
            logger.info(f"🚀 开始爬取单日数据: {start_date}")
            data = self.fetch_single_day(node_name, start_date)
            if data is None:
                return None
            all_data = data if data else []
        else:
            logger.info(f"🚀 开始爬取日期范围数据: {start_date} 至 {end_date}")
            all_data = self.fetch_date_range(node_name, start_date, end_date)

        # 保存数据
        if not all_data:
            logger.warning("⚠️ 没有数据可保存")
            return None

        # 根据格式保存
        if save_format.lower() == 'excel':
            filepath = FileHandler.save_to_excel(
                all_data,
                node_name=node_name,
                start_date=start_date,
                end_date=end_date
            )
        elif save_format.lower() == 'csv':
            filepath = FileHandler.save_to_csv(
                all_data,
                node_name=node_name,
                start_date=start_date,
                end_date=end_date
            )
        elif save_format.lower() == 'json':
            filepath = FileHandler.save_to_json(
                all_data,
                node_name=node_name,
                start_date=start_date,
                end_date=end_date
            )
        else:
            logger.error(f"❌ 不支持的保存格式: {save_format}")
            return None

        return filepath

    def test_connection(self) -> bool:
        """
        测试连接和Cookie是否有效

        Returns:
            bool: 是否有效
        """
        logger.info("🔍 测试连接和Cookie...")

        from utils.date_utils import get_current_date

        # 使用一个常见节点测试
        test_node = "华北.太钢/500kV.1母线"
        test_date = get_current_date()

        data = self.fetch_single_day(test_node, test_date)

        if data is not None:
            logger.info(f"✅ 连接测试成功！获取到 {len(data)} 条数据")
            return True
        else:
            logger.error("❌ 连接测试失败，请检查Cookie")
            return False

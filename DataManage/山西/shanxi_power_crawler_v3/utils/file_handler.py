"""
文件处理工具模块
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
from config.settings import EXCEL_DIR, CSV_DIR, JSON_DIR, EXCEL_ENGINE, CSV_ENCODING
from .logger import logger


class FileHandler:
    """文件处理类"""

    @staticmethod
    def save_to_excel(data: List[Dict], filename: str = None, node_name: str = None,
                      start_date: str = None, end_date: str = None) -> str:
        """
        保存数据到Excel文件

        Args:
            data: 数据列表
            filename: 文件名（可选）
            node_name: 节点名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 保存的文件路径
        """
        if not data:
            logger.warning("数据为空，不保存文件")
            return None

        try:
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_node_name = node_name.replace('/', '_').replace('.', '_') if node_name else "unknown"

                if start_date and end_date:
                    filename = f"日前节点电价_{safe_node_name}_{start_date}_至_{end_date}_{timestamp}.xlsx"
                else:
                    filename = f"日前节点电价_{safe_node_name}_{timestamp}.xlsx"

            filepath = os.path.join(EXCEL_DIR, filename)

            # 转换为DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine=EXCEL_ENGINE)

            file_size = os.path.getsize(filepath) / 1024
            logger.info(f"✅ 数据已保存到Excel: {filepath}")
            logger.info(f"📊 文件大小: {file_size:.2f} KB")
            logger.info(f"📈 数据行数: {len(df)}")
            logger.info(f"📋 数据列数: {len(df.columns)}")

            return filepath

        except Exception as e:
            logger.error(f"❌ 保存Excel失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def save_to_csv(data: List[Dict], filename: str = None, node_name: str = None,
                    start_date: str = None, end_date: str = None) -> str:
        """
        保存数据到CSV文件

        Args:
            data: 数据列表
            filename: 文件名（可选）
            node_name: 节点名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 保存的文件路径
        """
        if not data:
            logger.warning("数据为空，不保存文件")
            return None

        try:
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_node_name = node_name.replace('/', '_').replace('.', '_') if node_name else "unknown"

                if start_date and end_date:
                    filename = f"节点电价_{safe_node_name}_{start_date}_至_{end_date}_{timestamp}.csv"
                else:
                    filename = f"节点电价_{safe_node_name}_{timestamp}.csv"

            filepath = os.path.join(CSV_DIR, filename)

            # 转换为DataFrame并保存
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding=CSV_ENCODING)

            file_size = os.path.getsize(filepath) / 1024
            logger.info(f"✅ 数据已保存到CSV: {filepath}")
            logger.info(f"📊 文件大小: {file_size:.2f} KB")

            return filepath

        except Exception as e:
            logger.error(f"❌ 保存CSV失败: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def save_to_json(data: List[Dict], filename: str = None, node_name: str = None,
                     start_date: str = None, end_date: str = None) -> str:
        """
        保存数据到JSON文件

        Args:
            data: 数据列表
            filename: 文件名（可选）
            node_name: 节点名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            str: 保存的文件路径
        """
        if not data:
            logger.warning("数据为空，不保存文件")
            return None

        try:
            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_node_name = node_name.replace('/', '_').replace('.', '_') if node_name else "unknown"

                if start_date and end_date:
                    filename = f"节点电价_{safe_node_name}_{start_date}_至_{end_date}_{timestamp}.json"
                else:
                    filename = f"节点电价_{safe_node_name}_{timestamp}.json"

            filepath = os.path.join(JSON_DIR, filename)

            # 保存为JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            file_size = os.path.getsize(filepath) / 1024
            logger.info(f"✅ 数据已保存到JSON: {filepath}")
            logger.info(f"📊 文件大小: {file_size:.2f} KB")

            return filepath

        except Exception as e:
            logger.error(f"❌ 保存JSON失败: {str(e)}", exc_info=True)
            return None

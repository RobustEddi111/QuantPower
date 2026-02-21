"""
Cookie管理工具模块
"""

import json
from typing import Union, List, Dict
from .logger import logger


class CookieManager:
    """Cookie管理类"""

    @staticmethod
    def parse_cookies(cookies_input: Union[str, List[Dict]]) -> str:
        """
        解析Cookie为字符串格式

        Args:
            cookies_input: Cookie输入（字符串或JSON格式）

        Returns:
            str: Cookie字符串
        """
        try:
            # 如果已经是字符串格式
            if isinstance(cookies_input, str):
                # 尝试解析为JSON
                if cookies_input.strip().startswith('['):
                    try:
                        cookie_list = json.loads(cookies_input)
                        return CookieManager._list_to_string(cookie_list)
                    except json.JSONDecodeError:
                        # 如果解析失败，直接返回原字符串
                        return cookies_input
                else:
                    return cookies_input

            # 如果是列表格式
            elif isinstance(cookies_input, list):
                return CookieManager._list_to_string(cookies_input)

            else:
                logger.error(f"不支持的Cookie格式: {type(cookies_input)}")
                return ""

        except Exception as e:
            logger.error(f"解析Cookie失败: {str(e)}", exc_info=True)
            return ""

    @staticmethod
    def _list_to_string(cookie_list: List[Dict]) -> str:
        """
        将Cookie列表转换为字符串

        Args:
            cookie_list: Cookie列表

        Returns:
            str: Cookie字符串
        """
        try:
            cookie_pairs = []
            for item in cookie_list:
                if 'name' in item and 'value' in item:
                    cookie_pairs.append(f"{item['name']}={item['value']}")

            cookie_string = "; ".join(cookie_pairs)
            logger.debug(f"Cookie转换成功，共 {len(cookie_pairs)} 个")
            return cookie_string

        except Exception as e:
            logger.error(f"Cookie列表转换失败: {str(e)}", exc_info=True)
            return ""

    @staticmethod
    def validate_cookies(cookies: str) -> bool:
        """
        验证Cookie是否有效

        Args:
            cookies: Cookie字符串

        Returns:
            bool: 是否有效
        """
        if not cookies or not isinstance(cookies, str):
            return False

        # 简单验证：至少包含一个键值对
        if '=' not in cookies:
            return False

        return True

    @staticmethod
    def load_from_file(filepath: str) -> str:
        """
        从文件加载Cookie

        Args:
            filepath: 文件路径

        Returns:
            str: Cookie字符串
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            return CookieManager.parse_cookies(content)

        except Exception as e:
            logger.error(f"从文件加载Cookie失败: {str(e)}", exc_info=True)
            return ""

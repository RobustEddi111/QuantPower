"""
爬虫基类
"""

import requests
import time
from typing import Dict, Any, Optional
from config.settings import (
    BASE_URL, HEADERS, TIMEOUT, MAX_RETRIES,
    REQUEST_DELAY, USE_PROXY, PROXIES, COOKIE_EXPIRED_KEYWORDS
)
from utils.logger import logger  # ✅ 小写 logger
from utils.cookie_manager import CookieManager


class BaseCrawler:
    """爬虫基类"""

    def __init__(self, cookies: str = None):  # ✅ cookies 不是 pokies
        """
        初始化爬虫

        Args:
            cookies: Cookie字符串或JSON格式
        """
        self.base_url = BASE_URL
        self.timeout = TIMEOUT
        self.max_retries = MAX_RETRIES
        self.request_delay = REQUEST_DELAY

        # 解析Cookie
        if cookies:
            self.cookies = CookieManager.parse_cookies(cookies)
        else:
            self.cookies = ""

        # 设置请求头
        self.headers = HEADERS.copy()
        if self.cookies:
            self.headers['Cookie'] = self.cookies

        # 代理设置
        self.proxies = PROXIES if USE_PROXY else None

        logger.info("爬虫初始化完成")

    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求（带重试机制）

        Args:
            method: 请求方法（GET/POST）
            url: 请求URL
            **kwargs: 其他请求参数

        Returns:
            requests.Response: 响应对象，失败返回None
        """
        for attempt in range(self.max_retries):
            try:
                # 合并headers
                headers = self.headers.copy()
                if 'headers' in kwargs:
                    headers.update(kwargs.pop('headers'))

                # 发送请求
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.timeout,
                    proxies=self.proxies,
                    **kwargs
                )

                # 检查状态码
                if response.status_code == 200:
                    return response
                elif response.status_code in [401, 403]:
                    logger.error(f"❌ Cookie已失效，状态码: {response.status_code}")
                    return None
                else:
                    logger.warning(f"⚠️ HTTP错误: {response.status_code}")

            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ 请求超时，重试 {attempt + 1}/{self.max_retries}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ 请求异常: {str(e)}")
            except Exception as e:
                logger.error(f"❌ 未知错误: {str(e)}", exc_info=True)

            # 重试前等待
            if attempt < self.max_retries - 1:
                time.sleep(2)

        logger.error(f"❌ 请求失败，已重试 {self.max_retries} 次")
        return None

    def _check_response(self, response_data: Dict[str, Any]) -> bool:
        """
        检查响应数据是否有效

        Args:
            response_data: 响应数据

        Returns:
            bool: 是否有效
        """
        if not response_data:
            return False

        # 检查状态码
        status = response_data.get('status')
        if status != 0:
            message = response_data.get('message', '未知错误')

            # 检查是否Cookie失效
            if any(keyword in message for keyword in COOKIE_EXPIRED_KEYWORDS):
                logger.error(f"❌ Cookie已失效: {message}")
            else:
                logger.warning(f"⚠️ 接口返回错误: {message}")

            return False

        return True

    def get(self, url: str, **kwargs) -> Optional[Dict]:
        """
        发送GET请求

        Args:
            url: 请求URL
            **kwargs: 其他请求参数

        Returns:
            Dict: 响应JSON数据
        """
        response = self._make_request('GET', url, **kwargs)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"❌ 解析JSON失败: {str(e)}")
        return None

    def post(self, url: str, **kwargs) -> Optional[Dict]:
        """
        发送POST请求

        Args:
            url: 请求URL
            **kwargs: 其他请求参数

        Returns:
            Dict: 响应JSON数据
        """
        response = self._make_request('POST', url, **kwargs)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"❌ 解析JSON失败: {str(e)}")
        return None

    def sleep(self, seconds: float = None):
        """
        延迟执行

        Args:
            seconds: 延迟秒数，默认使用配置的REQUEST_DELAY
        """
        delay = seconds if seconds is not None else self.request_delay
        if delay > 0:
            time.sleep(delay)

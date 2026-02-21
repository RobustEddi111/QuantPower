
import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
import os

"""
定义ShanxiPowerPriceCrawler.class类文件
"""
class ShanxiPowerPriceCrawler:
    """山西电力交易中心爬虫"""

    def __init__(self, cookies):
        self.base_url = "https://pmos.sx.sgcc.com.cn/px-sy-retailsettlement-sx/resource/dayNodePrice"
        self.cookies = self._parse_cookies(cookies)
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Cookie': self.cookies,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://pmos.sx.sgcc.com.cn/',
            'Origin': 'https://pmos.sx.sgcc.com.cn'
        }

    def _parse_cookies(self, cookies_input):
        """解析Cookie"""
        if isinstance(cookies_input, str):
            if cookies_input.strip().startswith('['):
                # JSON格式
                try:
                    cookie_list = json.loads(cookies_input)
                    return "; ".join([f"{item['name']}={item['value']}" for item in cookie_list])
                except:
                    return cookies_input
            else:
                # 字符串格式
                return cookies_input
        return cookies_input

    def fetch_price_data(self, node_name, date_str, retry=3):
        """
        获取单日单节点的电价数据

        参数:
            node_name: 节点名称
            date_str: 日期字符串 (YYYY-MM-DD)
            retry: 重试次数

        返回:
            list: 数据列表，失败返回空列表，Cookie失效返回None
        """
        payload = {
            "data": {
                "nodeName": node_name,
                "atDate": date_str
            },
            "pageInfo": {
                "pageNum": 1,
                "pageSize": 100
            }
        }

        for attempt in range(retry):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=15
                )

                if response.status_code == 200:
                    result = response.json()

                    if result.get('status') == 0:
                        data_list = result.get('data', {}).get('list', [])
                        print(f"✅ {date_str} {node_name}: 获取 {len(data_list)} 条数据")
                        return data_list
                    else:
                        error_msg = result.get('message', '未知错误')
                        if '登录' in error_msg or '会话' in error_msg:
                            print(f"❌ Cookie已失效: {error_msg}")
                            return None
                        print(f"⚠️ 接口返回错误: {error_msg}")

                elif response.status_code in [401, 403]:
                    print(f"❌ Cookie已失效，状态码: {response.status_code}")
                    return None
                else:
                    print(f"⚠️ HTTP错误: {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"⚠️ 请求超时，重试 {attempt + 1}/{retry}")
            except Exception as e:
                print(f"⚠️ 请求异常: {str(e)}")

            if attempt < retry - 1:
                time.sleep(2)

        print(f"❌ {date_str} {node_name}: 获取失败")
        return []

    def crawl_date_range(self, node_name, start_date, end_date):
        """
        爬取日期范围内的数据

        参数:
            node_name: 节点名称
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        返回:
            DataFrame: 包含所有数据的DataFrame
        """
        print("=" * 70)
        print(f"📅 爬取日期范围: {start_date} 至 {end_date}")
        print(f"📍 节点名称: {node_name}")
        print("=" * 70)

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        all_data = []
        current = start

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            data = self.fetch_price_data(node_name, date_str)

            if data is None:
                print("\n❌ Cookie已失效，请重新获取Cookie后继续")
                break

            all_data.extend(data)
            current += timedelta(days=1)
            time.sleep(1)  # 避免请求过快

        if all_data:
            df = pd.DataFrame(all_data)
            print(f"\n✅ 共获取 {len(all_data)} 条数据")
            return df
        else:
            print("\n❌ 未获取到任何数据")
            return pd.DataFrame()

    def save_to_excel(self, df, filename):
        """
        保存数据到Excel文件

        参数:
            df: DataFrame对象
            filename: 文件名
        """
        if df.empty:
            print("⚠️ 数据为空，不保存文件")
            return

        try:
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\n💾 数据已保存到: {filename}")
            print(f"📊 文件大小: {os.path.getsize(filename) / 1024:.2f} KB")
            print(f"📈 数据行数: {len(df)}")
            print(f"📋 数据列数: {len(df.columns)}")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")

    def save_to_csv(self, df, filename):
        """
        保存数据到CSV文件

        参数:
            df: DataFrame对象
            filename: 文件名
        """
        if df.empty:
            print("⚠️ 数据为空，不保存文件")
            return

        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n💾 数据已保存到: {filename}")
            print(f"📊 文件大小: {os.path.getsize(filename) / 1024:.2f} KB")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
"""
山西电力交易中心 - 日前节点边际电价爬虫
功能：爬取指定节点的电价数据
作者：
版本：2.0
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
import os


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


# ==================== 主程序 ====================

def main():
    print("=" * 70)
    print("🚀 山西电力交易中心 - 日前节点边际电价爬虫")
    print("=" * 70)

    # 输入Cookie
    print("\n请粘贴Cookie（粘贴后输入END结束）：")
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
        return

    # 创建爬虫实例
    crawler = ShanxiPowerPriceCrawler(cookies_input)

    # 选择爬取模式
    print("\n" + "=" * 70)
    print("请选择爬取模式：")
    print("=" * 70)
    print("1. 单日单节点 - 查询某个节点某一天的数据")
    print("2. 日期范围单节点 - 查询某个节点一段时间的数据")
    print("=" * 70)

    mode = input("\n请选择模式 (1/2): ").strip()

    if mode == '1':
        # 单日单节点模式
        print("\n" + "=" * 70)
        print("📌 单日单节点模式")
        print("=" * 70)

        node_name = input("\n请输入节点名称（例如：华北.太钢/500kV.1母线）: ").strip()
        date_str = input("请输入日期（YYYY-MM-DD，例如：2026-02-18）: ").strip()

        print("\n开始爬取...")
        data = crawler.fetch_price_data(node_name, date_str)

        if data:
            df = pd.DataFrame(data)

            # 生成文件名
            safe_node_name = node_name.replace('/', '_').replace('.', '_')
            filename = f"电价数据_{safe_node_name}_{date_str}.xlsx"

            crawler.save_to_excel(df, filename)

            # 显示数据预览
            print("\n" + "=" * 70)
            print("📊 数据预览（前5行）：")
            print("=" * 70)
            print(df.head())
        else:
            print("\n❌ 未能获取数据")

    elif mode == '2':
        # 日期范围单节点模式
        print("\n" + "=" * 70)
        print("📌 日期范围单节点模式")
        print("=" * 70)

        node_name = input("\n请输入节点名称（例如：华北.太钢/500kV.1母线）: ").strip()
        start_date = input("请输入开始日期（YYYY-MM-DD）: ").strip()
        end_date = input("请输入结束日期（YYYY-MM-DD）: ").strip()

        print("\n开始爬取...")
        df = crawler.crawl_date_range(node_name, start_date, end_date)

        if not df.empty:
            # 生成文件名
            safe_node_name = node_name.replace('/', '_').replace('.', '_')
            filename = f"电价数据_{safe_node_name}_{start_date}_至_{end_date}.xlsx"

            crawler.save_to_excel(df, filename)

            # 显示数据预览
            print("\n" + "=" * 70)
            print("📊 数据预览（前5行）：")
            print("=" * 70)
            print(df.head())

            print("\n" + "=" * 70)
            print("📊 数据统计：")
            print("=" * 70)
            if 'price' in df.columns:
                print(f"平均电价: {df['price'].mean():.4f}")
                print(f"最高电价: {df['price'].max():.4f}")
                print(f"最低电价: {df['price'].min():.4f}")
        else:
            print("\n❌ 未能获取数据")

    else:
        print("\n❌ 无效的选择")

    print("\n" + "=" * 70)
    print("✅ 程序执行完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()

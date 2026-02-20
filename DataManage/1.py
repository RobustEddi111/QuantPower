# 创建一个单独的Python文件，包含所有代码
# 这样你只需要复制一个文件就能生成所有其他文件

all_in_one_code = '''"""
山西电力交易中心爬虫 - 一键生成所有文件
运行这个脚本会自动创建所有需要的文件
使用方法：python generate_all_files.py
"""

import os

# 创建项目目录
project_dir = "shanxi_power_crawler"
if not os.path.exists(project_dir):
    os.makedirs(project_dir)
    print(f"✅ 创建目录: {project_dir}")


# ==================== 文件2: config.py ====================
config_py = """\\"""
配置文件示例
可以在这里预设常用的节点名称和日期范围
\\"""

# 常用节点列表
COMMON_NODES = [
    "华北.太钢/500kV.1母线",
    "华北.电网/500kV母线",
    # 添加更多节点...
]

# 默认日期范围
DEFAULT_START_DATE = "2026-02-01"
DEFAULT_END_DATE = "2026-02-28"

# 请求设置
REQUEST_TIMEOUT = 15  # 请求超时时间（秒）
RETRY_TIMES = 3  # 重试次数
SLEEP_TIME = 1  # 请求间隔（秒）

# 输出设置
OUTPUT_DIR = "./output"  # 输出目录
OUTPUT_FORMAT = "excel"  # 输出格式：excel 或 csv
"""

with open(os.path.join(project_dir, "config.py"), "w", encoding="utf-8") as f:
    f.write(config_py)
print("✅ 创建文件: config.py")

# ==================== 文件3: quick_check_cookie.py ====================
quick_check_py = """\\"""
山西电力交易中心 - Cookie快速检测工具
功能：快速检测Cookie是否有效
作者：Monica
版本：1.0
\\"""

import requests
import json


def quick_check_cookie(cookies_input):
    \\"""
    快速检测Cookie是否有效
    \\"""
    print("="*70)
    print("🔍 正在检测Cookie有效性...")
    print("="*70)

    # 解析Cookie
    if cookies_input.strip().startswith('['):
        # JSON格式
        try:
            cookie_list = json.loads(cookies_input)
            cookie_string = "; ".join([f"{item['name']}={item['value']}" for item in cookie_list])
            print("✅ 识别为JSON格式")
        except Exception as e:
            print(f"❌ JSON格式解析失败: {e}")
            return False
    else:
        # 字符串格式
        cookie_string = cookies_input
        print("✅ 识别为字符串格式")

    # 测试请求
    url = "https://pmos.sx.sgcc.com.cn/px-sy-retailsettlement-sx/resource/dayNodePrice"

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Cookie': cookie_string,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    payload = {
        "data": {
            "nodeName": "华北.太钢/500kV.1母线",
            "atDate": "2026-02-18"
        },
        "pageInfo": {
            "pageNum": 1,
            "pageSize": 1
        }
    }

    try:
        print("\\n📡 正在发送测试请求...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        print(f"\\n📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if result.get('status') == 0:
                data_count = len(result.get('data', {}).get('list', []))
                print("\\n" + "="*70)
                print("✅ Cookie 有效！")
                print("="*70)
                print(f"📈 成功获取 {data_count} 条数据")
                print("🎉 可以开始爬取了！")
                return True
            else:
                print("\\n" + "="*70)
                print("❌ Cookie 已失效！")
                print("="*70)
                print(f"📌 错误信息: {result.get('message', '未知错误')}")
                return False

        elif response.status_code in [401, 403]:
            print("\\n" + "="*70)
            print("❌ Cookie 已失效！")
            print("="*70)
            return False

        else:
            print("\\n⚠️ 未知状态")
            return False

    except Exception as e:
        print(f"\\n❌ 请求异常: {str(e)}")
        return False


if __name__ == "__main__":
    print("="*70)
    print("🚀 Cookie快速检测工具")
    print("="*70)

    print("\\n请粘贴Cookie（粘贴后按Enter，然后输入END再按Enter）：")

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    cookies_input = '\\n'.join(lines).strip()

    if not cookies_input:
        print("❌ Cookie不能为空")
    else:
        quick_check_cookie(cookies_input)
"""

with open(os.path.join(project_dir, "quick_check_cookie.py"), "w", encoding="utf-8") as f:
    f.write(quick_check_py)
print("✅ 创建文件: quick_check_cookie.py")

# ==================== 文件4: shanxi_power_crawler.py ====================
# 由于代码太长，分段写入
crawler_py_part1 = """\\"""
山西电力交易中心 - 日前节点边际电价爬虫
功能：爬取指定节点的电价数据
作者：Monica
版本：2.0
\\"""

import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
import os


class ShanxiPowerPriceCrawler:
    \\"""山西电力交易中心爬虫\\"""

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
        if isinstance(cookies_input, str):
            if cookies_input.strip().startswith('['):
                try:
                    cookie_list = json.loads(cookies_input)
                    return "; ".join([f"{item['name']}={item['value']}" for item in cookie_list])
                except:
                    return cookies_input
            else:
                return cookies_input
        return cookies_input

    def fetch_price_data(self, node_name, date_str, retry=3):
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
        print("="*70)
        print(f"📅 爬取日期范围: {start_date} 至 {end_date}")
        print(f"📍 节点名称: {node_name}")
        print("="*70)

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        all_data = []
        current = start

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            data = self.fetch_price_data(node_name, date_str)

            if data is None:
                print("\\n❌ Cookie已失效，请重新获取Cookie后继续")
                break

            all_data.extend(data)
            current += timedelta(days=1)
            time.sleep(1)

        if all_data:
            df = pd.DataFrame(all_data)
            print(f"\\n✅ 共获取 {len(all_data)} 条数据")
            return df
        else:
            print("\\n❌ 未获取到任何数据")
            return pd.DataFrame()

    def save_to_excel(self, df, filename):
        if df.empty:
            print("⚠️ 数据为空，不保存文件")
            return

        try:
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\\n💾 数据已保存到: {filename}")
            print(f"📊 文件大小: {os.path.getsize(filename) / 1024:.2f} KB")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")


def main():
    print("="*70)
    print("🚀 山西电力交易中心 - 日前节点边际电价爬虫")
    print("="*70)

    print("\\n请粘贴Cookie（粘贴后输入END结束）：")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    cookies_input = '\\n'.join(lines).strip()

    if not cookies_input:
        print("❌ Cookie不能为空")
        return

    crawler = ShanxiPowerPriceCrawler(cookies_input)

    print("\\n请选择爬取模式：")
    print("1. 单日单节点")
    print("2. 日期范围单节点")

    mode = input("\\n请选择模式 (1/2): ").strip()

    if mode == '1':
        node_name = input("\\n请输入节点名称: ").strip()
        date_str = input("请输入日期（YYYY-MM-DD）: ").strip()

        data = crawler.fetch_price_data(node_name, date_str)
        if data:
            df = pd.DataFrame(data)
            filename = f"电价数据_{node_name.replace('/', '_')}_{date_str}.xlsx"
            crawler.save_to_excel(df, filename)

    elif mode == '2':
        node_name = input("\\n请输入节点名称: ").strip()
        start_date = input("请输入开始日期（YYYY-MM-DD）: ").strip()
        end_date = input("请输入结束日期（YYYY-MM-DD）: ").strip()

        df = crawler.crawl_date_range(node_name, start_date, end_date)
        if not df.empty:
            filename = f"电价数据_{node_name.replace('/', '_')}_{start_date}_至_{end_date}.xlsx"
            crawler.save_to_excel(df, filename)


if __name__ == "__main__":
    main()
"""

with open(os.path.join(project_dir, "shanxi_power_crawler.py"), "w", encoding="utf-8") as f:
    f.write(crawler_py_part1)
print("✅ 创建文件: shanxi_power_crawler.py")

# ==================== 文件5: README.md ====================
readme_md = """# 山西电力交易中心数据爬虫

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 检测Cookie
```bash
python quick_check_cookie.py
```

### 3. 开始爬取
```bash
python shanxi_power_crawler.py
```

## 📖 使用说明

### Cookie获取方法
1. 登录山西电力交易中心
2. 安装 EditThisCookie 浏览器扩展
3. 导出Cookie并复制

### 爬取模式
- **单日单节点**: 查询单个节点某一天的数据
- **日期范围单节点**: 查询单个节点一段时间的数据

## ⚠️ 注意事项
- Cookie有效期约30分钟
- 建议分批爬取大量数据
- 保持浏览器登录状态

## 📞 问题反馈
如遇问题，请检查：
1. Python版本 >= 3.7
2. 依赖包已安装
3. Cookie是否有效
4. 网络连接正常
"""

with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_md)
print("✅ 创建文件: README.md")

print("\\n" + "="*70)
print("🎉 所有文件创建完成！")
print("="*70)
print(f"📂 项目目录: {project_dir}")
print("\\n包含以下文件：")
print("  1. requirements.txt - 依赖包列表")
print("  2. config.py - 配置文件")
print("  3. quick_check_cookie.py - Cookie检测工具")
print("  4. shanxi_power_crawler.py - 主爬虫程序")
print("  5. README.md - 使用说明")
print("\\n✨ 现在可以开始使用了！")
print("="*70)
'''

# 保存到文件
output_file = '/home/user/generate_all_files.py'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(all_in_one_code)

print("=" * 70)
print("✅ 已生成一键安装脚本！")
print("=" * 70)
print(f"\n📄 文件名: generate_all_files.py")
print(f"📊 大小: {os.path.getsize(output_file) / 1024:.2f} KB")
print("\n🎯 使用方法：")
print("  1. 下载这个文件")
print("  2. 运行: python generate_all_files.py")
print("  3. 自动生成所有需要的文件！")
print("=" * 70)

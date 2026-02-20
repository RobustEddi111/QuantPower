"""
电力现货电价数据爬虫 - 复用已登录浏览器 (修复版)
"""

import requests
import json
import urllib3
import os
import time
from datetime import datetime
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PowerPriceScraperBrowser:
    """复用浏览器会话的爬虫"""

    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies = {'http': None, 'https': None}

        # 清空代理环境变量
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            os.environ[key] = ''

        self.base_url = 'https://pmos.xj.sgcc.com.cn:20080'
        self.cookies = {}
        self.headers = {}

    def parse_curl_command(self, curl_command):
        """解析 curl 命令"""
        print("\n正在解析 curl 命令...")

        result = {
            'url': None,
            'cookies': {},
            'headers': {}
        }

        try:
            # 提取 URL
            url_patterns = [
                r"curl '([^']+)'",
                r'curl "([^"]+)"',
                r"curl ([^\s\\]+)"
            ]

            for pattern in url_patterns:
                match = re.search(pattern, curl_command)
                if match:
                    result['url'] = match.group(1)
                    print(f"✓ URL: {result['url'][:80]}...")
                    break

            # 提取 Cookies (-b 参数)
            cookie_patterns = [
                r"-b '([^']+)'",
                r'-b "([^"]+)"',
                r"--cookie '([^']+)'",
                r'--cookie "([^"]+)"'
            ]

            for pattern in cookie_patterns:
                match = re.search(pattern, curl_command)
                if match:
                    cookie_str = match.group(1)
                    for item in cookie_str.split('; '):
                        if '=' in item:
                            key, value = item.split('=', 1)
                            result['cookies'][key.strip()] = value.strip()
                    print(f"✓ Cookies: {len(result['cookies'])} 个")
                    break

            # 提取 Headers (-H 参数) - 修复正则表达式
            header_patterns = [
                r"-H '([^']+)'",
                r'-H "([^"]+)"'
            ]

            for pattern in header_patterns:
                for match in re.finditer(pattern, curl_command):
                    header_line = match.group(1)
                    if ':' in header_line:
                        key, value = header_line.split(':', 1)
                        result['headers'][key.strip()] = value.strip()

            print(f"✓ Headers: {len(result['headers'])} 个")

            # 显示提取的 Headers
            if result['headers']:
                print("\n提取的请求头:")
                for key, value in list(result['headers'].items())[:5]:
                    print(f"  {key}: {value[:50]}...")

            return result

        except Exception as e:
            print(f"✗ 解析失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_cookies_from_browser(self):
        """从浏览器更新 Cookies"""
        print("="*70)
        print("📋 请按以下步骤操作:")
        print("="*70)
        print("\n1. 在浏览器中确保已登录电力交易中心")
        print("2. 打开电价数据页面")
        print("3. 按 F12 打开开发者工具")
        print("4. 切换到 Network (网络) 标签")
        print("5. 刷新页面 (F5)")
        print("6. 找到任意一个请求（状态码 200）")
        print("7. 右键 -> Copy -> Copy as cURL (bash)")
        print("8. 粘贴到下面:")
        print("\n" + "-"*70)

        # 读取多行输入
        print("请粘贴 curl 命令 (可以多行，粘贴完成后输入空行):")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)

        curl_command = ' '.join(lines)

        if not curl_command:
            print("✗ 未输入 curl 命令")
            return False

        # 解析 curl 命令
        parsed = self.parse_curl_command(curl_command)

        if not parsed or not parsed['url']:
            print("✗ 解析失败，未能提取到 URL")
            return False

        self.cookies = parsed['cookies']
        self.headers = parsed['headers']

        # 更新 session
        self.session.cookies.update(self.cookies)
        self.session.headers.update(self.headers)

        # 保存配置
        config = {
            'url': parsed['url'],
            'cookies': self.cookies,
            'headers': self.headers,
            'timestamp': datetime.now().isoformat()
        }

        with open('browser_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print("\n✓ 配置已保存到 browser_config.json")

        return True

    def load_config(self):
        """加载保存的配置"""
        try:
            with open('browser_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.cookies = config.get('cookies', {})
            self.headers = config.get('headers', {})

            self.session.cookies.update(self.cookies)
            self.session.headers.update(self.headers)

            timestamp = config.get('timestamp', 'unknown')
            print(f"✓ 已加载配置 (保存时间: {timestamp})")
            print(f"  Cookies: {len(self.cookies)} 个")
            print(f"  Headers: {len(self.headers)} 个")

            return True

        except FileNotFoundError:
            print("✗ 未找到配置文件 browser_config.json")
            return False
        except Exception as e:
            print(f"✗ 加载配置失败: {e}")
            return False

    def fetch_data(self, url=None):
        """获取数据"""
        if not url:
            # 尝试从配置文件读取
            try:
                with open('browser_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    url = config.get('url')
            except:
                pass

        if not url:
            print("✗ 未指定 URL")
            return None

        print("\n" + "="*70)
        print("开始获取数据")
        print("="*70)
        print(f"\nURL: {url[:100]}...")
        print(f"Cookies: {len(self.cookies)} 个")
        print(f"Headers: {len(self.headers)} 个")

        try:
            response = self.session.get(url, timeout=30)

            print(f"\n✓ 收到响应")
            print(f"  状态码: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"  大小: {len(response.content)} 字节")

            if response.status_code == 200:
                # 尝试解析 JSON
                content_type = response.headers.get('Content-Type', '')

                if 'json' in content_type:
                    data = response.json()

                    # 保存数据
                    filename = f'power_price_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    print(f"\n✅ 数据获取成功！")
                    print(f"✓ 已保存到: {filename}")

                    # 显示数据摘要
                    if isinstance(data, dict):
                        print(f"\n数据类型: 字典")
                        print(f"字段: {list(data.keys())}")

                        # 显示前几条数据
                        print(f"\n数据预览:")
                        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                        print("...")

                    elif isinstance(data, list):
                        print(f"\n数据类型: 列表")
                        print(f"数据条数: {len(data)}")
                        if len(data) > 0:
                            print(f"第一条: {data[0]}")

                    return data
                else:
                    # HTML 或其他格式
                    filename = f'power_price_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)

                    print(f"\n✓ 响应已保存到: {filename}")
                    print(f"\n内容预览:\n{response.text[:500]}")

                    return {'raw': response.text}

            elif response.status_code == 412:
                print("\n❌ 412 错误 - Cookie 已过期")
                print("请重新从浏览器复制 curl 命令")
                return None

            elif response.status_code == 400:
                print("\n❌ 400 错误 - 请求参数无效")
                print(f"响应内容: {response.text}")
                print("\nURL 中的参数可能已过期，请:")
                print("  1. 在浏览器中刷新页面")
                print("  2. 重新复制最新的 curl 命令")
                return None

            else:
                print(f"\n❌ 请求失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"\n✗ 请求异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    def monitor_mode(self, interval=60):
        """监控模式 - 定期获取数据"""
        print("\n" + "="*70)
        print("🔄 监控模式")
        print("="*70)
        print(f"\n每 {interval} 秒获取一次数据")
        print("按 Ctrl+C 停止\n")

        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取数据...")

                result = self.fetch_data()

                if result:
                    print(f"✓ 成功")
                else:
                    print(f"✗ 失败 - Cookie 可能已过期")
                    print("请重新运行程序并更新 curl 命令")
                    break

                print(f"\n等待 {interval} 秒...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✓ 已停止监控")


def main():
    """主函数"""
    print("="*70)
    print("电力现货电价数据爬取工具 v3.1")
    print("="*70)
    print("\n✓ 已禁用代理\n")

    scraper = PowerPriceScraperBrowser()

    # 检查是否有保存的配置
    if os.path.exists('browser_config.json'):
        print("发现已保存的配置文件\n")
        print("请选择:")
        print("  1. 使用已保存的配置")
        print("  2. 重新从浏览器获取配置")

        choice = input("\n请输入选项 (1/2): ").strip()

        if choice == '1':
            if scraper.load_config():
                result = scraper.fetch_data()

                if result:
                    print("\n✅ 数据获取成功！")

                    # 询问是否启动监控模式
                    monitor = input("\n是否启动监控模式？(y/n): ").strip().lower()
                    if monitor == 'y':
                        interval = input("输入监控间隔（秒，默认60）: ").strip()
                        interval = int(interval) if interval.isdigit() else 60
                        scraper.monitor_mode(interval)
                else:
                    print("\n❌ 数据获取失败")
                    print("Cookie 可能已过期，请重新从浏览器获取")
            return

    # 从浏览器获取新配置
    if scraper.update_cookies_from_browser():
        result = scraper.fetch_data()

        if result:
            print("\n✅ 数据获取成功！")

            # 询问是否启动监控模式
            monitor = input("\n是否启动监控模式？(y/n): ").strip().lower()
            if monitor == 'y':
                interval = input("输入监控间隔（秒，默认60）: ").strip()
                interval = int(interval) if interval.isdigit() else 60
                scraper.monitor_mode(interval)
        else:
            print("\n❌ 数据获取失败")
    else:
        print("\n❌ 配置更新失败")


if __name__ == "__main__":
    main()
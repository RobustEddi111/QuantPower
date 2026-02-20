"""
山西电力交易中心 - Cookie快速检测工具
功能：快速检测Cookie是否有效
作者：Monica
版本：1.0
"""

import requests
import json


def quick_check_cookie(cookies_input):
    """
    快速检测Cookie是否有效
    """
    print("=" * 70)
    print("🔍 正在检测Cookie有效性...")
    print("=" * 70)

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
        print("\n📡 正在发送测试请求...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        print(f"\n📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"📊 响应内容预览: {str(result)[:200]}...")

            if result.get('status') == 0:
                data_count = len(result.get('data', {}).get('list', []))
                print("\n" + "=" * 70)
                print("✅ Cookie 有效！")
                print("=" * 70)
                print(f"📈 成功获取 {data_count} 条数据")
                print("🎉 可以开始爬取了！")
                return True
            else:
                print("\n" + "=" * 70)
                print("❌ Cookie 已失效！")
                print("=" * 70)
                print(f"📌 错误信息: {result.get('message', '未知错误')}")
                print("\n🔄 请重新获取Cookie：")
                print("  1. 在浏览器中重新登录")
                print("  2. 使用 EditThisCookie 导出Cookie")
                print("  3. 粘贴到程序中")
                return False

        elif response.status_code in [401, 403]:
            print("\n" + "=" * 70)
            print("❌ Cookie 已失效！")
            print("=" * 70)
            print(f"📌 HTTP状态码: {response.status_code} (未授权)")
            print("\n🔄 请重新获取Cookie")
            return False

        else:
            print("\n" + "=" * 70)
            print("⚠️ 未知状态")
            print("=" * 70)
            print(f"📌 HTTP状态码: {response.status_code}")
            print(f"📌 响应内容: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("\n❌ 请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败，请检查网络或VPN")
        return False
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")
        return False


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Cookie快速检测工具")
    print("=" * 70)
    print("\n支持格式：")
    print("  1. EditThisCookie的JSON格式")
    print("  2. 标准Cookie字符串")
    print("\n" + "=" * 70)

    print("\n请粘贴Cookie（粘贴后按Enter，然后输入END再按Enter）：")

    # 多行输入
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
    else:
        quick_check_cookie(cookies_input)

    print("\n" + "=" * 70)
    print("检测完成！")
    print("=" * 70)

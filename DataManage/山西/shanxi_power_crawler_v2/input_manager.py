# input_manager.py
"""
智能输入管理 - 支持配置文件和交互输入
"""

import os
import json
from datetime import datetime
from config import *


class InputManager:
    """管理用户输入和配置"""

    @staticmethod
    def get_cookies():
        """获取Cookie - 优先级: 配置文件 > 环境变量 > 交互输入"""

        # 1. 从配置文件读取
        if COOKIES:
            print("✅ 使用配置文件中的Cookie")
            return COOKIES

        # 2. 从Cookie文件读取
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                    cookie_content = f.read().strip()
                    if cookie_content:
                        print(f"✅ 从 {COOKIE_FILE} 读取Cookie")
                        return cookie_content
            except Exception as e:
                print(f"⚠️ 读取Cookie文件失败: {e}")

        # 3. 交互输入
        print("\n📝 请输入Cookie（支持JSON格式或字符串格式）")
        print("提示: 输入END结束，或按Ctrl+D")
        print("-" * 50)

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

        # 询问是否保存
        if cookies_input:
            save = input("\n💾 是否保存Cookie到文件？(y/n): ").lower()
            if save == 'y':
                InputManager.save_cookies(cookies_input)

        return cookies_input

    @staticmethod
    def save_cookies(cookies):
        """保存Cookie到文件"""
        try:
            with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
                f.write(cookies)
            print(f"✅ Cookie已保存到 {COOKIE_FILE}")
            print("⚠️ 注意: 请妥善保管Cookie文件，不要泄露！")
        except Exception as e:
            print(f"❌ 保存失败: {e}")

    @staticmethod
    def get_nodes():
        """获取节点列表"""

        if RUN_MODE == 'auto' and USE_DEFAULT_NODES:
            print(f"✅ 使用默认节点: {DEFAULT_NODES}")
            return DEFAULT_NODES

        # 交互输入
        print("\n📍 请选择节点输入方式:")
        print("1. 使用默认节点")
        print("2. 手动输入节点")
        print("3. 从文件读取")

        choice = input("请选择 (1-3): ").strip()

        if choice == '1':
            return DEFAULT_NODES

        elif choice == '2':
            print("\n请输入节点名称（每行一个，输入END结束）:")
            nodes = []
            while True:
                node = input().strip()
                if node.upper() == 'END':
                    break
                if node:
                    nodes.append(node)
            return nodes

        elif choice == '3':
            filename = input("请输入节点文件路径: ").strip()
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    nodes = [line.strip() for line in f if line.strip()]
                print(f"✅ 从 {filename} 读取 {len(nodes)} 个节点")
                return nodes
            except Exception as e:
                print(f"❌ 读取失败: {e}")
                return []

        return []

    @staticmethod
    def get_date_range():
        """获取日期范围"""

        if RUN_MODE == 'auto' and USE_DEFAULT_DATES:
            print(f"✅ 使用默认日期: {DEFAULT_START_DATE} 至 {DEFAULT_END_DATE}")
            return DEFAULT_START_DATE, DEFAULT_END_DATE

        # 交互输入
        print("\n📅 请选择日期输入方式:")
        print("1. 使用默认日期范围")
        print("2. 手动输入日期")

        choice = input("请选择 (1-2): ").strip()

        if choice == '1':
            return DEFAULT_START_DATE, DEFAULT_END_DATE

        else:
            start_date = input("请输入开始日期 (YYYY-MM-DD): ").strip()
            end_date = input("请输入结束日期 (YYYY-MM-DD): ").strip()
            return start_date, end_date

    @staticmethod
    def get_run_mode():
        """获取运行模式"""

        if RUN_MODE == 'auto':
            return AUTO_MODE_OPTION

        # 交互选择
        print("\n" + "=" * 70)
        print("🎯 请选择运行模式:")
        print("=" * 70)
        print("1. 单日数据爬取")
        print("2. 日期范围爬取")
        print("3. 批量节点爬取")
        print("-" * 70)

        mode = input("请选择模式 (1-3): ").strip()
        return int(mode) if mode.isdigit() else 1

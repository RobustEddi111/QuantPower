
# 📄 `README.md`


# 山西电力交易中心 - 日前节点边际电价爬虫 v3.0

> 专业的电力交易数据采集工具，支持批量爬取山西电力交易中心的日前节点边际电价数据

---

## ✨ 特性

- 🚀 **模块化设计** - 清晰的项目结构，易于维护和扩展
- 📊 **多种保存格式** - 支持 Excel、CSV、JSON 格式导出
- 🔄 **智能重试机制** - 自动重试失败的请求，提高稳定性
- 📅 **灵活的日期选择** - 支持单日、日期范围、最近N天、当月数据爬取
- 🍪 **Cookie管理** - 支持多种Cookie格式输入
- 📝 **完善的日志** - 详细的运行日志，方便问题排查
- 🎯 **节点配置** - 内置1000+真实节点，支持快速查询
- ⚡ **交互式界面** - 友好的命令行交互，操作简单

---

## 📦 项目结构

```
shanxi_power_node_price_crawler/
├── config/                      # 配置模块
│   ├── __init__.py
│   └── settings.py              # 全局配置
├── crawler/                     # 爬虫模块
│   ├── __init__.py
│   ├── base_crawler.py          # 爬虫基类
│   └── node_price_crawler.py   # 节点电价爬虫
├── utils/                       # 工具模块
│   ├── __init__.py
│   ├── logger.py                # 日志工具
│   ├── date_utils.py            # 日期工具
│   ├── file_handler.py          # 文件处理
│   └── cookie_manager.py        # Cookie管理
├── data/                        # 数据目录
│   ├── excel/                   # Excel文件
│   ├── csv/                     # CSV文件
│   └── json/                    # JSON文件
├── logs/                        # 日志目录
├── nodes.json                   # 节点配置文件（1086个真实节点）
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖包
└── README.md                    # 项目说明
```

---

## 🛠️ 安装

### 1. 克隆项目

```bash
git clone <repository_url>
cd shanxi_power_node_price_crawler
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install requests pandas openpyxl python-dateutil
```

### 3. 验证安装

```bash
python main.py
```

---

## 🚀 快速开始

### 1. 获取 Cookie

在浏览器中登录山西电力交易中心网站后：

**方法一：使用 EditThisCookie 插件**
1. 安装 Chrome 插件 [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/)
2. 点击插件图标 → 导出 → 复制 JSON 格式的 Cookie

**方法二：使用浏览器开发者工具**
1. 按 F12 打开开发者工具
2. 切换到 Network 标签
3. 刷新页面，找到任意请求
4. 在 Headers 中找到 Cookie，复制整个字符串

### 2. 运行程序

```bash
python main.py
```

### 3. 输入 Cookie

程序启动后，按提示粘贴 Cookie，输入 `END` 结束。

### 4. 选择功能

根据菜单提示选择需要的功能：

```
1. 爬取单日单节点数据
2. 爬取日期范围单节点数据
3. 爬取最近 N 天数据
4. 爬取当前月份数据
5. 查看常用节点列表
6. 测试 Cookie 是否有效
0. 退出程序
```

---

## 📖 使用示例

### 示例 1：爬取单日数据

```
请选择功能: 1
请输入节点名称: 华北.太钢/500kV.1母线
请输入日期 (YYYY-MM-DD) [默认: 2026-02-21]: 2026-02-18
保存格式 (excel/csv/json) [默认: excel]: excel
确认开始爬取? (y/n) [默认: y]: y
```

### 示例 2：爬取日期范围

```
请选择功能: 2
请输入节点名称: 华北.晋城/500kV.1母线
请输入开始日期 (YYYY-MM-DD): 2026-02-01
请输入结束日期 (YYYY-MM-DD): 2026-02-20
保存格式 (excel/csv/json) [默认: excel]: excel
确认开始爬取? (y/n) [默认: y]: y
```

### 示例 3：爬取最近7天

```
请选择功能: 3
请输入节点名称: 华北.阳泉/500kV.1母线
请输入天数 [默认: 7]: 7
保存格式 (excel/csv/json) [默认: excel]: excel
确认开始爬取? (y/n) [默认: y]: y
```

### 示例 4：爬取当前月份

```
请选择功能: 4
请输入节点名称: 华北.临汾/500kV.1母线
保存格式 (excel/csv/json) [默认: excel]: excel
确认开始爬取? (y/n) [默认: y]: y
```

---

## 🔧 配置说明

### config/settings.py

可以根据需要修改以下配置：

```python
# 请求配置
TIMEOUT = 15                # 请求超时时间（秒）
MAX_RETRIES = 3             # 最大重试次数
REQUEST_DELAY = 1           # 请求间隔（秒）
PAGE_SIZE = 100             # 分页大小

# 代理配置
USE_PROXY = False           # 是否使用代理
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

# 日志配置
LOG_LEVEL = "INFO"          # 日志级别
```

---

## 📊 数据说明

### 数据字段

爬取的数据包含以下字段（具体字段以实际返回为准）：

- `nodeName` - 节点名称
- `atDate` - 日期
- `price` - 电价
- `isDay` - 是否日前
- `generatorName` - 发电厂名称
- 其他字段...

### 数据存储

数据保存在 `data/` 目录下：

- **Excel 格式**: `data/excel/节点电价_节点名称_日期.xlsx`
- **CSV 格式**: `data/csv/节点电价_节点名称_日期.csv`
- **JSON 格式**: `data/json/节点电价_节点名称_日期.json`

---

## 📝 节点列表

### 常用节点

项目内置了 **1086 个真实节点**，包括：

#### 1000kV 特高压节点
- 华北.北岳/1000kV.1母线
- 华北.洪善/1000kV.1母线
- 国调.长治站/1000kV.1母线

#### 500kV 节点
- 华北.太钢/500kV.1母线
- 华北.晋城/500kV.1母线
- 华北.阳泉/500kV.1母线
- 华北.临汾/500kV.1母线
- 华北.运城/500kV.1母线
- 更多节点请查看 `nodes.json`

#### 220kV 节点（按地区分类）
- 太原地区
- 大同地区
- 阳泉地区
- 长治地区
- 晋城地区
- 临汾地区
- 运城地区

#### 新能源节点
- 光伏电站（100+ 个）
- 风电场（100+ 个）
- 储能电站（10+ 个）

**查看完整节点列表**：
- 运行程序后选择功能 `5`
- 或直接查看 `nodes.json` 文件

---

## 🔍 日志说明

### 日志文件

日志保存在 `logs/` 目录下：

- `crawler_YYYYMMDD.log` - 普通日志（INFO级别）
- `error_YYYYMMDD.log` - 错误日志（ERROR级别）

### 日志级别

- **DEBUG** - 详细的调试信息
- **INFO** - 一般信息（默认）
- **WARNING** - 警告信息
- **ERROR** - 错误信息

---

## ⚠️ 常见问题

### 1. Cookie 失效

**现象**：提示 "Cookie已失效" 或 "登录" 相关错误

**解决**：
1. 重新登录山西电力交易中心网站
2. 获取新的 Cookie
3. 重新运行程序

### 2. 请求超时

**现象**：提示 "请求超时"

**解决**：
1. 检查网络连接
2. 增加 `TIMEOUT` 配置值
3. 检查是否需要使用代理

### 3. 数据为空

**现象**：爬取成功但数据为空

**原因**：
- 该节点在指定日期没有数据
- 节点名称输入错误

**解决**：
1. 确认节点名称是否正确
2. 尝试其他日期
3. 使用功能 `5` 查看可用节点列表

### 4. 保存文件失败

**现象**：提示 "保存失败"

**解决**：
1. 检查 `data/` 目录是否有写入权限
2. 确认磁盘空间充足
3. 关闭可能占用文件的程序（如 Excel）

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件

---

## 🙏 致谢

感谢山西电力交易中心提供的数据接口。

---

## 📅 更新日志

### v3.0 (2026-02-21)
- ✨ 全新模块化架构
- ✨ 支持多种保存格式（Excel/CSV/JSON）
- ✨ 新增交互式菜单
- ✨ 内置1086个真实节点
- ✨ 完善的日志系统
- ✨ Cookie管理优化
- ✨ 智能重试机制

### v2.0 (2026-02-18)
- ✨ 支持日期范围爬取
- ✨ 优化Cookie解析
- ✨ 改进错误处理

### v1.0 (2026-02-15)
- 🎉 初始版本发布
- ✨ 基础爬取功能

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
```

---

## 🎉 项目完成！

所有文件已生成完毕！现在让我为你总结一下：

---

## 📦 完整项目文件清单

| 序号 | 文件路径 | 说明 |
|------|---------|------|
| 1 | `config/__init__.py` | 配置模块初始化 |
| 2 | `config/settings.py` | 全局配置文件 |
| 3 | `nodes.json` | 1086个真实节点配置 |
| 4 | `utils/__init__.py` | 工具模块初始化 |
| 5 | `utils/logger.py` | 日志工具 |
| 6 | `utils/date_utils.py` | 日期工具 |
| 7 | `utils/file_handler.py` | 文件处理工具 |
| 8 | `utils/cookie_manager.py` | Cookie管理工具 |
| 9 | `crawler/__init__.py` | 爬虫模块初始化 |
| 10 | `crawler/base_crawler.py` | 爬虫基类 |
| 11 | `crawler/node_price_crawler.py` | 节点电价爬虫 |
| 12 | `main.py` | 主程序入口 |
| 13 | `requirements.txt` | 依赖包列表 |
| 14 | `README.md` | 项目说明文档 |

---

## 🚀 使用步骤

### 1️⃣ 创建项目目录结构

```bash
mkdir -p shanxi_power_node_price_crawler/{config,crawler,utils,data/{excel,csv,json},logs}
cd shanxi_power_node_price_crawler
```

### 2️⃣ 复制所有代码文件

将上面生成的所有文件内容复制到对应位置。

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 4️⃣ 运行程序

```bash
python main.py
```

---

## ✨ 项目亮点

1. **模块化设计** - 清晰的分层架构
2. **完整的工具链** - 日志、日期、文件、Cookie管理
3. **真实节点数据** - 1086个真实节点
4. **交互式界面** - 友好的命令行交互
5. **多种保存格式** - Excel/CSV/JSON
6. **智能重试** - 自动重试失败请求
7. **详细日志** - 完善的日志记录
8. **灵活配置** - 易于定制和扩展

---

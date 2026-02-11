"""
用于节点电价数据格式、字段统一
统一甘肃数据格式-->山西格式
"""
import os
import re
import glob
import calendar
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict

# ========= 文件路径需要改这里 =========
DATA_DIR = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\甘肃2025年节点电价数据\甘肃2025年节电电价数据(全)"
OUT_DIR  = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\甘肃2025年节点电价数据\甘肃2025年节电电价数据标准化Schema"
# =================================
os.makedirs(OUT_DIR, exist_ok=True)

# 1.路径读取
data_dir=DATA_DIR
data_dir = data_dir.strip()

try:
    print("DATA_DIR =", data_dir)
    print("原始文件目录前30个条目：", os.listdir(data_dir)[:30])
except Exception as e:
    raise FileNotFoundError(f"目录无法访问：{data_dir}，错误：{e}")

patterns = ["**/*.csv", "**/*.xlsx", "**/*.xls", "**/*.xlsm"]
files = []
for p in patterns:
    files += glob.glob(os.path.join(data_dir, p), recursive=True)
files = sorted(set(files))

print(f"扫描到原始文件夹文件数量（含CSV/Excel）：{len(files)}")
print("原始文件夹示例前5个文件：", files[:5])

if not files:
    raise FileNotFoundError(f"未找到CSV/Excel（含子文件夹）：{data_dir}")

# 原始文件名解析
def parse_filename_to_json(filename: str) -> Dict[str, str]:
    """
    解析文件名，提取：
      - node: 日期前的整段（如：甘肃飞鸿变330kV330kV I 母）
      - date_start/date_end: 起止日期
      - market: 日前/实时

    适配示例：
      甘肃飞鸿变330kV330kV I 母-2025-01-01-2025-12-31日前节点出清电价.csv
      甘肃甘州变330kV330kVⅡ母-2025-01-01-2025-12-31实时节点出清电价.csv
    """
    base = os.path.basename(filename).strip()

    # 去掉扩展名
    if base.lower().endswith(".csv"):
        base = base[:-4]

    # 规范化一些常见字符（可按需增删）
    base = (base
            .replace("　", " ")   # 全角空格
            .strip())

    # 用“日期段 + 日前/实时”做锚点
    m = re.search(
        r"-(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})(日前|实时)",
        base
    )
    if not m:
        raise ValueError(f"无法从文件名解析日期与日前/实时：{filename}")

    date_start, date_end, market = m.group(1), m.group(2), m.group(3)

    # 节点名称/标识段：从开头到日期段开始位置
    node = base[:m.start()].strip()

    return {
        "node": node,
        "date_start": date_start,
        "date_end": date_end,
        "market": market,
        "raw_filename": os.path.basename(filename),
    }

# 2.定义原文件df字段、新文件df字段
df_new = pd.DataFrame(columns=['节点名称', '日期', '时点', '电能量价格（元/MWh）', '阻塞价格（元/MWh）','节点电价（元/MWh）'])

# 3.文件及文件名读取，原文件df数据读取
for file in files:
    df_origin=pd.read_csv(file)
    df_new['节点名称']=df_origin['tag']
    df_new['日期']=df_origin['date']
    df_new['时点']=df_origin['time']
    df_new['电能量价格（元/MWh）']=df_origin.iloc[:,5]
    df_new['阻塞价格（元/MWh）']=df_origin.iloc[:,6]
    df_new['节点电价（元/MWh）']=df_origin.iloc[:,1]

    file_name = Path(file).name  # 提取文件名
    result=parse_filename_to_json(file_name)
    fname=result["market"]+result["node"]+"_"+result["date_start"]+"-"+result["date_end"]+"节点边际电价"
    dir_path = OUT_DIR # 输出文件路径
    # 确保目录存在（如果 fname 含路径）
    path_file_new=os.path.join(dir_path,fname+".csv")

    df_new.to_csv(path_file_new, index=False, encoding="utf-8-sig")










# 4.完成新文件df转换


# 5.完成导出csv














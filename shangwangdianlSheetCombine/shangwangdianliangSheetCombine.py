import pandas as pd
import re
import os
from datetime import datetime
from constant.CONSTANT import dataPath

# 文件夹路径，包含所有要处理的Excel文件
folder_path = dataPath
###
# 定义一个正则表达式，匹配以数字开头并以"日"结尾的工作表名称
pattern = re.compile(r'^\d+日$')

# 创建一个空的DataFrame用于存放所有合并后的数据
combined_df = pd.DataFrame()

# 遍历文件夹中的每一个Excel文件
for file_name in os.listdir(folder_path):
    if file_name.endswith('.xlsx'):
        file_path = os.path.join(folder_path, file_name)
        # 使用ExcelFile读取文件
        xls = pd.ExcelFile(file_path)

        # 遍历Excel文件中的每一个工作表
        for sheet_name in xls.sheet_names:
            # 如果工作表名匹配固定的格式（1日, 2日, ..., 30日）
            if pattern.match(sheet_name):
                # 读取符合条件的工作表
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # 将数据追加到combined_df中
                combined_df = pd.concat([combined_df, df], ignore_index=True)
# 获取当前时间作为文件名的一部分
current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
print(current_time)
# 指定导出文件夹路径
output_folder = dataPath

# 构造带有当前时间的文件名
output_file = os.path.join(output_folder, f'汇总导出上网电量_{current_time}.xlsx')


# 将合并后的数据写入到一个新的Excel文件
combined_df.to_excel(output_file, index=False)
print("--------完成合并-------------")
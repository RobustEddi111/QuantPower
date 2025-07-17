import pandas as pd

# 读取工作簿

file_path = 'D:\\工作\\特变电工\\05工作报告\\限电率分析报告\\1-12月中长期分配系数\\中长期分配系数统计表2024年1-12月.xlsx'  # 修改为实际的文件路径
workbook = pd.ExcelFile(file_path)
# 创建一个新的字典来保存修改后的数据
sheets_dict = {}

# 遍历工作簿中的所有表
for sheet_name in workbook.sheet_names:
    df = workbook.parse(sheet_name)

    # 假设日期列从第3列开始，且每两个日期列有一个分数和一个百分比分数
    # 第1列是我方单元的名称，第2列是同区域单元的名称
    # 删除百分比分数列，即每个偶数列
    cols_to_drop = []
    for i in range(3, len(df.columns), 2):  # 从第3列开始，步长为2
        cols_to_drop.append(df.columns[i])

    # 删除列
    df = df.drop(cols_to_drop, axis=1)

    #     # 为每个分数列进行区域排名
    #     for i in range(3, len(df.columns)):  # 从第3列(即第一个分数列)开始
    #         # 确保分数列为数值类型，非数值的转换为NaN
    #         df[df.columns[i]] = pd.to_numeric(df[df.columns[i]], errors='coerce')

    #         # 对同区域单元分组后排名
    #         df[f'Rank_{df.columns[i]}'] = df.groupby(df.columns[1])[df.columns[i]].transform(
    #             lambda x: x.rank(ascending=False, method='min'))

    # 将修改后的表存入字典
    sheets_dict[sheet_name] = df



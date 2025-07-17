import pandas as pd
import re
import constant.CONSTANT


def delete_row(inputFile,sheetName,outputFile):
    # 读取 Excel 文件并选择指定工作表
    df = pd.read_excel(inputFile, sheetName, header=1)
    # 打印工作表中的数据
    # print(df)
    print(
        "----------------------------------------------------------------\n---------------------------------------------------------")
    pattern = r'\b发电事业部.*电站报表\b'
    i = 0
    for index, row in df.iterrows():
        # print("Index:", index)
        # print("Row:", row)
        if index > 2 and (pattern == row[0] or "序号" == row[0]):
            continue
        else:
            row_dict = row.to_dict()
            df_row = pd.DataFrame.from_dict(row_dict, orient="index").T
            # 将第一次出现的保留行作为新表开头记录
            if (i == 0):
                df_rows = df_row
                i += 1
                continue
            df_rows = pd.concat([df_rows, df_row], ignore_index=True)
    print(df_rows)
    # TODO：需要指定df_rows写入outputFile文件路径并写入


inputFile=constant.CONSTANT.dataPath
sheetName = constant.CONSTANT.ownerDataSheet  # 要选择的工作表名称

delete_row(inputFile,sheetName,outputFile)










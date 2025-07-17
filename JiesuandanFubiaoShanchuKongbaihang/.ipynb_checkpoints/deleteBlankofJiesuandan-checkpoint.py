import pandas as pd
import re
import constant.CONSTANT
import os

def delete_row(inputFile, sheetName, outputFile):
    # 读取 Excel 文件并选择指定工作表
    df = pd.read_excel(inputFile, sheetName, header=1)
    # 打印工作表中的数据
    print(
        "----------------------------------------------------------------\n---------------------------------------------------------")

    # 正则表达式匹配以“交易结算明细”或“交易明细”结尾的行
    pattern_settlement = re.compile(r'.*交易结算明细$')
    pattern_transaction = re.compile(r'.*交易明细$')

    i = 0
    for index, row in df.iterrows():
        if index > 2 and (
                pattern_settlement.match(str(row[0])) or
                pattern_transaction.match(str(row[0])) or
                "附表" == row[0] or
                "结算科目编码" == row[0] or
                "单位：兆瓦时、兆瓦、元/兆瓦时、元/兆瓦、元"==row[0]
        ):
            continue
        else:
            row_dict = row.to_dict()
            df_row = pd.DataFrame.from_dict(row_dict, orient="index").T
            # 将第一次出现的保留行作为新表开头记录
            if i == 0:
                df_rows = df_row
                i += 1
                continue
            df_rows = pd.concat([df_rows, df_row], ignore_index=True)

    df_rows = df_rows.iloc[1:].reset_index(drop=True)  # 删除旧表头行并重置索引

    # 打印最终的 DataFrame
    print(df_rows)

    # 将结果写入指定的输出文件
    df_rows.to_excel(outputFile, index=False)
    print(f"数据已写入 {outputFile}")





# inputFile = constant.CONSTANT.dataPath
# sheetName = constant.CONSTANT.ownerDataSheet  # 要选择的工作表名称
# outputFile = constant.CONSTANT.outputFile
# delete_row(inputFile, sheetName, outputFile)

def process_folder(inputFolder, sheetName, outputFolder):
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

    for file_name in os.listdir(inputFolder):
        if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            inputFile = os.path.join(inputFolder, file_name)
            outputFile = os.path.join(outputFolder, "已删除空行_" + file_name)
            delete_row(inputFile, sheetName, outputFile)


inputFolder = constant.CONSTANT.inputFolder
sheetName = constant.CONSTANT.ownerDataSheet  # 要选择的工作表名称
outputFolder = constant.CONSTANT.outputFolder
process_folder(inputFolder, sheetName, outputFolder)


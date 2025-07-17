import csv

def delete_csv_row(input_file, output_file):
    # 读取原始CSV文件
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        origin_rows = list(reader)
        rows = list()

    # 删除指定行
    for index, row in enumerate(origin_rows):
        if index > 2 and ("日电站报表" in row[0] or "序号" in row[0]):
            print(row)
        else:
            rows.append(row)

    # 将更新后的内容写入新的CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)


# 调用函数删除CSV文件中的第三行（索引从0开始）
delete_csv_row('D:\Test\Test1.CSV', 'D:\Test\output.csv')


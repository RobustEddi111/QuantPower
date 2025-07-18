import pandas as pd
import re

# 合同序列类
class ContractData:
    def __init__(self, name, quantity, price, revenue):
        self.name = name  # 合同名称
        self.quantity = quantity  # 第一行，24小时电量
        self.price = price  # 第二行，24小时价格
        self.revenue = revenue  # 第三行，24小时费用

    def total_quantity(self):
        return self.quantity.sum()

    def total_revenue(self):
        return self.revenue.sum()

    def avg_price(self):
        return (self.price * self.quantity).sum() / self.quantity.sum()

    def __repr__(self):
        return (
            f"<ContractData name={self.name} "
            f"总量={self.total_quantity():.2f} "
            f"加权均价={self.avg_price():.2f} "
            f"总费用={self.total_revenue():.2f}>"
        )


# 市场分摊及返还费用类
class SpecialItemData:
    def __init__(self, frRev, fr_allocation_Cost, unitPenaltyCostRecovery, unitPenaltyCostAllocation,
                 GenMidLongRecovery, GenMidLongAllocation,
                 ConsumerMidLongAllocation, ConsumerSpotAllocation):
        self.frRev = frRev  # 调频辅助服务里程收益
        self.fr_allocation_Cost = fr_allocation_Cost  # 调频辅助服务费用分摊
        self.unitPenaltyCostRecovery = unitPenaltyCostRecovery  # 机组考核费用-回收
        self.unitPenaltyCostAllocation = unitPenaltyCostAllocation  # 机组考核费用-分摊
        self.GenMidLongRecovery = GenMidLongRecovery  # 发电侧中长期偏差收益回收-回收
        self.GenMidLongAllocation = GenMidLongAllocation  # 发电侧中长期偏差收益回收-分摊
        self.ConsumerMidLongAllocation = ConsumerMidLongAllocation  # 用户侧中长期偏差收益回收-分摊
        self.ConsumerSpotAllocation = ConsumerSpotAllocation  # 用户侧现货偏差收益回收-分摊


# 定义场站日清分数据类
class StationDayData:
    def __init__(self, station_name, date, generation, contracts, specail_item):
        self.station_name = station_name  # 场站名称
        self.date = date  # 清分日期
        self.generation = generation  # 上网数据
        self.contracts = contracts  # List of ContractData
        self.specail_item = specail_item  # 市场分摊及返还费用

    def get_product_by_name(self, name):
        for p in self.contracts:
            if p.name == name:
                return p
        return None


# 定义所有场站日清分汇总数据类
class PowerDataBook:
    def __init__(self):
        # data 是一个嵌套字典：{station_name: {date: StationDayData}}
        self.data = {}  # dict[station_name][date] = StationDayData

    def add_station_day_data(self, station_day_data):
        """添加一条站点的某天数据"""
        s = station_day_data.station_name  # 场站名称
        d = station_day_data.date  # 日期
        if s not in self.data:
            self.data[s] = {}  # 不包含场站时，创建新场站
        self.data[s][d] = station_day_data  # 添加场站s在d日的日清分数据


## dd

if __name__ == '__main__':
    # 设定文件路径（文件名中包含中文）
    filename = 'D:/工作/特变电工/01政策/_全国_20250520/国网区域/新疆/400-交易复盘/现货日清分_系统导出数据/哈密市振超风力发电有限公司2025-04-27-明细.xlsx'

    # 读取 Excel 文件（默认读取第一个 Sheet）
    df = pd.read_excel(filename)
    # 读取场站名称
    station_name = df.iloc[1, 1]
    # print("电站名称是：", station_name)

    # 用正则匹配“年-月-日”格式
    match = re.search(r'\d{4}-\d{2}-\d{2}', filename)
    if match:
        date_str = match.group()
        # print("提取的日期是：", date_str)
    else:
        print("未找到日期")
    generation = df.iloc[3]

    ContractDf = df.iloc[4:-8]  # 获取df中的中长期合同序列数据
    ContractDf.columns = ["名称"] + [f"{i}:00" for i in range(1, 25)] + ["合计"]
    ContractList = []  # 构造列表容器，准备将合同装入
    ContractDf
    for i in range(0, len(ContractDf), 3):
        name = ContractDf.iloc[i, 0]  # 从第 i 行第0列 提取合同序列名称
        quantity = ContractDf.iloc[i, 1:]  # 合同量
        price = ContractDf.iloc[i + 1, 1:]  # 合同价
        revenue = ContractDf.iloc[i + 2, 1:]  # 合同费用
        contract = ContractData(name, quantity, price, revenue)  # 封装成对象
        ContractList.append(contract)

    print(ContractList)

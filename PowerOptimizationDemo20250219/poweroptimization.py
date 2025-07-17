from gurobipy import Model, GRB, quicksum
import numpy as np

# 创建模型
model = Model("EconomicDispatch")

# 参数设置
T = 96  # 96个时段
hours_per_period = 0.25  # 15分钟转换为小时

# 火电机组参数（示例数据）
gen1 = {
    'Pmin': 30,  # 最小出力 (MW)
    'Pmax': 200,  # 最大出力 (MW)
    'a': 0.01,  # 成本系数 ($/MW²)
    'b': 2.0,  # 成本系数 ($/MW)
    'c': 100.0,  # 固定成本 ($)
    'ramp': 100  # 爬坡率 (MW/h)
}

gen2 = {
    'Pmin': 50,
    'Pmax': 250,
    'a': 0.02,
    'b': 1.5,
    'c': 80.0,
    'ramp': 80
}

# 生成模拟数据
np.random.seed(42)
load = 500 + 100 * np.sin(2 * np.pi * np.arange(T) / 24)  # 负荷曲线
wind = np.random.uniform(150, 250, T)  # 风电预测

# 定义决策变量
p1 = model.addVars(T, lb=gen1['Pmin'], ub=gen1['Pmax'], name="Gen1")
p2 = model.addVars(T, lb=gen2['Pmin'], ub=gen2['Pmax'], name="Gen2")
w = model.addVars(T, ub=wind, name="Wind")

# 电力平衡约束
model.addConstrs(
    (p1[t] + p2[t] + w[t] == load[t] for t in range(T)),
    name="PowerBalance"
)

# 爬坡率约束（转换为15分钟间隔）
for t in range(1, T):
    # 机组1
    delta_max1 = gen1['ramp'] * hours_per_period
    model.addConstr(p1[t] - p1[t - 1] <= delta_max1, f"RampUp_Gen1_{t}")
    model.addConstr(p1[t - 1] - p1[t] <= delta_max1, f"RampDown_Gen1_{t}")

    # 机组2
    delta_max2 = gen2['ramp'] * hours_per_period
    model.addConstr(p2[t] - p2[t - 1] <= delta_max2, f"RampUp_Gen2_{t}")
    model.addConstr(p2[t - 1] - p2[t] <= delta_max2, f"RampDown_Gen2_{t}")

# 目标函数（总运行成本）
total_cost = quicksum(
    gen1['a'] * p1[t] * p1[t] + gen1['b'] * p1[t] + gen1['c'] +
    gen2['a'] * p2[t] * p2[t] + gen2['b'] * p2[t] + gen2['c']
    for t in range(T)
)
model.setObjective(total_cost, GRB.MINIMIZE)

# 求解模型
model.optimize()

# 结果输出
if model.status == GRB.OPTIMAL:
    print(f"最优总成本: ${model.ObjVal:.2f}")

    # 提取结果
    p1_opt = [p1[t].X for t in range(T)]
    p2_opt = [p2[t].X for t in range(T)]
    w_opt = [w[t].X for t in range(T)]

    # 打印前5个时段结果
    print("\n时段 负荷需求 火电1 火电2 风电")
    for t in range(5):
        print(f"{t + 1:3d} {load[t]:7.2f} {p1_opt[t]:7.2f} {p2_opt[t]:7.2f} {w_opt[t]:7.2f}")
else:
    print("未找到最优解")
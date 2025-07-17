from gurobipy import Model, GRB

# 输入数据
demand = [500, 600, 700, 800]  # 各时段的负荷需求 (MW)
wind_forecast = [300, 400, 350, 450]  # 各时段风电预测出力 (MW)
hydro_max = [200, 200, 200, 200]  # 水电最大出力 (MW)
hydro_min = [50, 50, 50, 50]  # 水电最小出力 (MW)
thermal_max = [400, 400, 400, 400]  # 火电最大出力 (MW)
thermal_min = [100, 100, 100, 100]  # 火电最小出力 (MW)
thermal_ramp = 100  # 火电机组最大爬坡速率 (MW/h)
thermal_cost = 50  # 火电单位发电成本 (元/MWh)
hydro_cost = 10  # 水电调节成本 (元/MWh)
wind_spill_cost = 20  # 弃风成本 (元/MWh)

# 创建模型
model = Model("Power_Scheduling")

# 决策变量
n = len(demand)  # 时段数
thermal = model.addVars(n, lb=thermal_min, ub=thermal_max, name="thermal")  # 火电出力
hydro = model.addVars(n, lb=hydro_min, ub=hydro_max, name="hydro")  # 水电出力
wind_spill = model.addVars(n, lb=0, ub=wind_forecast, name="wind_spill")  # 弃风量

# 目标函数：最小化总成本
model.setObjective(
    sum(thermal_cost * thermal[t] + hydro_cost * hydro[t] + wind_spill_cost * wind_spill[t] for t in range(n)),
    GRB.MINIMIZE
)

# 约束条件
# 1. 功率平衡约束
for t in range(n):
    model.addConstr(
        thermal[t] + hydro[t] + (wind_forecast[t] - wind_spill[t]) == demand[t],
        name=f"balance_{t}"
    )

# 2. 火电机组爬坡约束
for t in range(1, n):
    model.addConstr(thermal[t] - thermal[t - 1] <= thermal_ramp, name=f"ramp_up_{t}")
    model.addConstr(thermal[t - 1] - thermal[t] <= thermal_ramp, name=f"ramp_down_{t}")

# 3. 弃风限制
for t in range(n):
    model.addConstr(wind_spill[t] <= wind_forecast[t], name=f"wind_spill_{t}")

# 求解
model.optimize()

# 输出结果
if model.status == GRB.OPTIMAL:
    print("Optimal Solution Found!")
    print("Thermal Power Output:", [thermal[t].X for t in range(n)])
    print("Hydro Power Output:", [hydro[t].X for t in range(n)])
    print("Wind Spillage:", [wind_spill[t].X for t in range(n)])
    print("Total Cost:", model.ObjVal)
else:
    print("No optimal solution found!")

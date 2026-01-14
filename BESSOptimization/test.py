# -*- coding: utf-8 -*-
"""
Gurobi 储能充放电套利（MILP）自检脚本
- 目标：最大化电价套利收益
- 约束：SOC 动态、充放电互斥、功率限额、SOC 边界、效率
"""

import sys
import traceback

try:
    import gurobipy as gp
    from gurobipy import GRB
except Exception as e:
    print("❌ 导入 gurobipy 失败：", e)
    print("👉 说明：当前 PyCharm 解释器环境里可能没装 gurobipy")
    sys.exit(1)


def run_storage_arbitrage():
    # ====== 你可以改这些参数 ======
    T = 24  # 时段数（比如 24小时；你也可以改成 96）
    dt = 1.0  # 每时段小时数；96点通常 dt=0.25

    # 示例电价（元/MWh 或 任意单位，只要前后一致）
    # 你也可以换成自己的价格序列（长度=T）
    price = [
        260, 250, 240, 235, 230, 225,
        230, 250, 320, 380, 420, 450,
        460, 440, 410, 380, 360, 340,
        330, 320, 310, 300, 290, 280
    ][:T]

    E_max = 100.0   # 储能容量（MWh）
    P_max = 50.0    # 充/放最大功率（MW）
    eta_c = 0.95    # 充电效率
    eta_d = 0.95    # 放电效率

    soc0 = 50.0     # 初始 SOC（MWh）
    soc_min = 10.0
    soc_max = 100.0

    # 是否要求期末SOC回到初始（常见：日内套利）
    enforce_terminal_soc = True

    # ====== 建模 ======
    m = gp.Model("storage_arbitrage_test")

    # 决策变量
    p_ch = m.addVars(T, lb=0.0, ub=P_max, name="p_ch")   # 充电功率
    p_dis = m.addVars(T, lb=0.0, ub=P_max, name="p_dis") # 放电功率
    soc = m.addVars(T, lb=soc_min, ub=soc_max, name="soc")

    # 互斥：同一时段不能同时充放（MILP）
    y_ch = m.addVars(T, vtype=GRB.BINARY, name="y_ch")
    y_dis = m.addVars(T, vtype=GRB.BINARY, name="y_dis")

    # 互斥约束
    for t in range(T):
        m.addConstr(p_ch[t] <= P_max * y_ch[t], name=f"ch_on_{t}")
        m.addConstr(p_dis[t] <= P_max * y_dis[t], name=f"dis_on_{t}")
        m.addConstr(y_ch[t] + y_dis[t] <= 1, name=f"mutex_{t}")

    # SOC 动态
    # soc[t] = soc[t-1] + eta_c * p_ch[t]*dt - (1/eta_d) * p_dis[t]*dt
    for t in range(T):
        if t == 0:
            m.addConstr(
                soc[t] == soc0 + eta_c * p_ch[t] * dt - (1.0 / eta_d) * p_dis[t] * dt,
                name="soc_0"
            )
        else:
            m.addConstr(
                soc[t] == soc[t-1] + eta_c * p_ch[t] * dt - (1.0 / eta_d) * p_dis[t] * dt,
                name=f"soc_{t}"
            )

    if enforce_terminal_soc:
        m.addConstr(soc[T-1] == soc0, name="terminal_soc")

    # 目标：最大化套利收益（放电卖电 - 充电买电）
    # 收益 = Σ price[t]*(p_dis - p_ch)*dt
    m.setObjective(gp.quicksum(price[t] * (p_dis[t] - p_ch[t]) * dt for t in range(T)), GRB.MAXIMIZE)

    # 求解参数（可选）
    m.Params.OutputFlag = 1  # 1=打印日志，0=静默
    m.Params.MIPGap = 1e-6

    # ====== 求解 ======
    m.optimize()

    # ====== 结果输出 ======
    if m.Status == GRB.OPTIMAL:
        print("\n✅ 求解成功：OPTIMAL")
        print("目标值(套利收益)：", m.ObjVal)
        print("\n时段 | 价格 | 充电(MW) | 放电(MW) | SOC(MWh)")
        for t in range(T):
            print(f"{t:>3d} | {price[t]:>4.0f} | {p_ch[t].X:>8.2f} | {p_dis[t].X:>8.2f} | {soc[t].X:>8.2f}")
    else:
        print("\n⚠️ 未得到最优解，状态码：", m.Status)


if __name__ == "__main__":
    try:
        print("Python:", sys.version)
        print("gurobipy version:", gp.__version__)
        print("Gurobi version:", gp.gurobi.version())
        run_storage_arbitrage()
    except gp.GurobiError as e:
        print("\n❌ GurobiError（很可能是 license 问题/环境变量问题）：")
        print(e)
        print("\n👉 常见原因：license 过期 / 找不到 license / 版本不匹配 / 没装 optimizer 本体")
    except Exception:
        print("\n❌ 其他异常：")
        traceback.print_exc()

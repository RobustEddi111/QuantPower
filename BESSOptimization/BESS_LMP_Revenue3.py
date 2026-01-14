# -*- coding: utf-8 -*-
"""
BESS 节点电价套利收益测算（Gurobi版）- 月策略口径B（一个月一套策略 + 月均价收益）
说明：
- 对每个 node + market + month，先构造 96点“月代表性价格曲线”（同一slot的月均价）
- 在该代表曲线上优化出“月策略”（一套96点充/放电功率）
- 月收益用“代表曲线收益 × 当月天数”计算（期望收益口径）
- 输出投决级Excel：月度Top10、实时-日前差异Top10、全量对比、月策略96点

依赖：
pip install pandas openpyxl gurobipy tqdm gurobi gurobipy
"""

import os
import re
import glob
import calendar
import pandas as pd
from datetime import datetime

import gurobipy as gp
from gurobipy import GRB
from tqdm import tqdm


# ========= 文件路径需要改这里 =========
DATA_DIR = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\山西2025年节电电价数据"
OUT_DIR  = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\山西2025年节电电价数据储能收益测算-按月分时"
# =================================
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 储能参数（按投决口径自行修改） ----------
P_MW = 100.0          # 功率 MW
E_MWH = 200.0         # 容量 MWh
ETA_C = 0.95          # 充电效率
ETA_D = 0.95          # 放电效率
SOC_MIN = 0.10 * E_MWH
SOC_MAX = 0.90 * E_MWH
SOC0_FRAC = 0.50      # 每天初始SOC占比（并要求日末回到初值）
DT_H = 0.25           # 15min=0.25h
# P_MW：充/放电功率上限（MW）。
#
# E_MWH：电池能量容量（MWh）。
#
# ETA_C / ETA_D：充电效率/放电效率（SOC 更新用）。
#
# SOC_MIN / SOC_MAX：SOC上下限（以 MWh 表示，不是百分比）。
#
# SOC0_FRAC：每天初始 SOC 占容量比例；并且模型要求日末 SOC 回到初值（策略闭合）。
#
# DT_H：时间步长（15分钟=0.25小时）。

# 可选：限制每日等效循环次数EFC（0=不启用该参数），例如 1.0 / 2.0# MAX_EQ_CYCLES_PER_DAY：每日等效循环上限（0 表示不限制）。
MAX_EQ_CYCLES_PER_DAY = 0

# 输出 TopN
TOPN = 10
# TOPN：输出 top10。

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """识别列：日期、时点、价格（节点电价/边际电价/LMP/电能量价）并标准化为 date/time/price/ts (+node占位)"""
   # 函数加单下划线_表示内部函数，只能用于同文件/同模块调用
   #  去掉列名空格，防止 “节点电价 ” 这种带尾空格导致识别失败。
    df = df.rename(columns={c: str(c).strip() for c in df.columns})

    # 工具函数：在当前表头中找包含某些关键词的列名。
    def pick_col(candidates):
        for key in candidates:
            for c in df.columns:
                if key in str(c):
                    return c
        return None

    # 找出节点列、日期列、时点列（若不存在节点列也允许）。
    col_node = pick_col(["节点名称", "节点", "Node"])
    col_date = pick_col(["日期", "date", "Date"])
    col_time = pick_col(["时点", "时间", "Time"])
    # 依次尝试不同命名方式找到价格列（兼容不同导出文件）。
    col_price = pick_col(["节点电价", "节点电价（元/MWh）"])
    if col_price is None:
        col_price = pick_col(["边际电价", "LMP", "节点边际电价"])
    if col_price is None:
        col_price = pick_col(["电能量价格", "电能量价", "能量价格"])

    # 日期 / 时点 / 价格缺任何一个就报错（这个文件就会被记录到 bad_files）。
    if not all([col_date, col_time, col_price]):
        raise ValueError(f"表头无法识别：date={col_date}, time={col_time}, price={col_price}")
    # 只保留必要列（避免杂列影响）
    use_cols = [c for c in [col_node, col_date, col_time, col_price] if c is not None]
    df = df[use_cols].copy()
    # 统一列名为：node / date / time / price。
    rename_map = {}
    if col_node is not None:
        rename_map[col_node] = "node"
    rename_map[col_date] = "date"
    rename_map[col_time] = "time"
    rename_map[col_price] = "price"
    df = df.rename(columns=rename_map)

    # 价格转数字，不能转的变NaN并删除。
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    # 日期转成真正日期，无法解析的删掉。
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])
    # 解析time（重点）
    def parse_time(x):
        if pd.isna(x):
            return None
        if isinstance(x, (datetime, pd.Timestamp)):
            return x.time()
        s = str(x).strip()
        # Excel 时间比例
        try:
            if re.fullmatch(r"\d+(\.\d+)?", s):
                frac = float(s)
                if 0 <= frac < 1:
                    total_minutes = int(round(frac * 24 * 60))
                    hh = total_minutes // 60
                    mm = total_minutes % 60
                    return datetime(2000, 1, 1, hh, mm).time()
        except Exception:
            pass
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).time()
            except Exception:
                continue
        return None

    df["time"] = df["time"].apply(parse_time)
    df = df.dropna(subset=["time"])
    # 把time列标准化，解析失败的删掉。
    df["ts"] = df.apply(lambda r: datetime.combine(r["date"], r["time"]), axis=1)

    if "node" not in df.columns:
        df["node"] = None
    # 按时间排序，返回标准格式
    df = df.sort_values(["ts"]).reset_index(drop=True)
    return df


def _infer_market_and_node_from_filename(fp: str):
    """从文件名识别 market(DA/RT/UNK) 与 node_id（文件名去掉日前/实时+日期段+指标）"""
    fname = os.path.basename(fp)
    # 用文件名前缀识别市场：日前 / 实时。
    if fname.startswith("日前"):
        market = "DA"
    elif fname.startswith("实时"):
        market = "RT"
    else:
        market = "UNK"

    node_id = fname.replace("日前", "").replace("实时", "")
    if "_2025-" in node_id:
        node_id = node_id.split("_2025-")[0]
    node_id = node_id.replace("节点边际电价", "")
    node_id = node_id.replace(".csv", "").replace(".xlsx", "").replace(".xls", "").replace(".xlsm", "")
    node_id = node_id.strip("_- ").strip()
    return market, node_id, fname


def read_folder(data_dir: str) -> pd.DataFrame:
    data_dir = data_dir.strip()

    try:
        print("DATA_DIR =", data_dir)
        print("根目录前30个条目：", os.listdir(data_dir)[:30])
    except Exception as e:
        raise FileNotFoundError(f"目录无法访问：{data_dir}，错误：{e}")

    patterns = ["**/*.csv", "**/*.xlsx", "**/*.xls", "**/*.xlsm"]
    files = []
    for p in patterns:
        files += glob.glob(os.path.join(data_dir, p), recursive=True)
    files = sorted(set(files))

    print(f"扫描到文件数量（含CSV/Excel）：{len(files)}")
    print("示例前5个文件：", files[:5])

    if not files:
        raise FileNotFoundError(f"未找到CSV/Excel（含子文件夹）：{data_dir}")

    all_df = []
    bad_files = []

    for fp in files:
        try:
            if fp.lower().endswith(".csv"):
                try:
                    raw = pd.read_csv(fp, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    raw = pd.read_csv(fp, encoding="gbk")
                if raw.shape[1] == 1:
                    raw = pd.read_csv(fp, encoding="utf-8-sig", sep=None, engine="python")
            else:
                raw = pd.read_excel(fp, sheet_name=0)

            df = _normalize_columns(raw)

            market, node_id, fname = _infer_market_and_node_from_filename(fp)
            df["market"] = market
            df["node"] = node_id  # ✅ 以文件名为准
            df["source_file"] = fname

            all_df.append(df)
            print(f"[OK] {fname} rows={len(df)}读取成功")

        except Exception as e:
            bad_files.append((fp, str(e), os.path.getsize(fp) if os.path.exists(fp) else None))
            print(f"[SKIP] {os.path.basename(fp)} 读取失败：{e}")

    if bad_files:
        bad_path = os.path.join(OUT_DIR, "bad_files.csv")
        pd.DataFrame(bad_files, columns=["file", "error", "size_bytes"]).to_csv(bad_path, index=False, encoding="utf-8-sig")
        print(f"已输出异常文件清单：{bad_path}")

    if not all_df:
        raise RuntimeError("扫描到文件但全部读取失败：检查CSV表头/分隔符/编码或Excel结构。")

    return pd.concat(all_df, ignore_index=True)


def optimize_profile_gurobi(prices_mwh_96):
    """
    在 96点价格曲线上求“代表日”最优套利策略（MILP），返回：
    - 策略：p_ch_mw[96], p_dis_mw[96]
    - 代表日统计：charge_mwh, discharge_mwh, eq_cycles, 平均充/放电价, 平均充/放电功率（活跃时段）
    - 代表日收益：profit_day_yuan（在该月均价曲线下）
    """
    if len(prices_mwh_96) != 96:
        raise ValueError("optimize_profile_gurobi 需要 96 点价格序列")

    T = 96
    soc0 = SOC0_FRAC * E_MWH
    eps = 1e-6

    # 建Gurobi模型，关闭求解日志
    m = gp.Model("bess_month_profile")
    m.Params.OutputFlag = 0

    p_ch = m.addVars(T, lb=0.0, ub=P_MW, vtype=GRB.CONTINUOUS, name="p_ch")
    p_dis = m.addVars(T, lb=0.0, ub=P_MW, vtype=GRB.CONTINUOUS, name="p_dis")
    soc = m.addVars(T + 1, lb=SOC_MIN, ub=SOC_MAX, vtype=GRB.CONTINUOUS, name="soc")
    y = m.addVars(T, vtype=GRB.BINARY, name="y")
    # p_ch[t]：t时段充电功率
    #
    # p_dis[t]：t时段放电功率
    #
    # soc[t]：时段开始时SOC（MWh），所以有T + 1个点
    #
    # y[t]：状态变量，互斥开关（二进制），保证同一时段不同时充放(y[t]=1-->t时刻充电，y[t]=0-->t时刻放电)

    m.setObjective(
        gp.quicksum(prices_mwh_96[t] * (p_dis[t] * DT_H - p_ch[t] * DT_H) for t in range(T)),
        GRB.MAXIMIZE
    )

    m.addConstr(soc[0] == soc0, name="soc_init")
    for t in range(T):
        m.addConstr(soc[t + 1] == soc[t] + p_ch[t] * DT_H * ETA_C - p_dis[t] * DT_H / ETA_D, name=f"soc_{t}")
        m.addConstr(p_ch[t] <= P_MW * y[t], name=f"mutex_ch_{t}")  #mutual exclusion（互斥）
        m.addConstr(p_dis[t] <= P_MW * (1 - y[t]), name=f"mutex_dis_{t}")
    m.addConstr(soc[T] == soc0, name="soc_end")

    # 每日循环充放电约束
    if MAX_EQ_CYCLES_PER_DAY and MAX_EQ_CYCLES_PER_DAY > 0:
        m.addConstr(gp.quicksum(p_dis[t] * DT_H for t in range(T)) <= MAX_EQ_CYCLES_PER_DAY * E_MWH, name="cycle_cap")

    m.optimize()

    if m.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {
            "status": f"STATUS_{m.Status}",
            "profit_day_yuan": 0.0,
            "charge_mwh_day": 0.0,
            "discharge_mwh_day": 0.0,
            "eq_cycles_day": 0.0,
            "avg_charge_price": 0.0,
            "avg_discharge_price": 0.0,
            "avg_ch_power_active_mw": 0.0,
            "avg_dis_power_active_mw": 0.0,
            "p_ch_mw": [0.0] * 96,
            "p_dis_mw": [0.0] * 96,
            "ch_active_intervals": 0,
            "dis_active_intervals": 0,
            "charge_value_yuan_day": 0.0,
            "discharge_value_yuan_day": 0.0,
        }

    p_ch_list = [float(p_ch[t].X) for t in range(T)]
    p_dis_list = [float(p_dis[t].X) for t in range(T)]

    """
    并逐时段累计：
    charge_mwh：总充电能量（MWh）
    discharge_mwh：总放电能量（MWh）
    charge_value：∑ price × 充电能量（用于能量加权充电电价）
    discharge_value：∑ price × 放电能量（用于能量加权放电电价）
    ch_active/dis_active：充/放发生的时段数
    sum_p_ch/sum_p_dis：活跃时段功率求和
    """
    charge_mwh = 0.0
    discharge_mwh = 0.0
    charge_value = 0.0
    discharge_value = 0.0

    ch_active = 0
    dis_active = 0
    sum_p_ch = 0.0
    sum_p_dis = 0.0

    for t in range(T):
        pch = p_ch_list[t]
        pdis = p_dis_list[t]
        pr = float(prices_mwh_96[t])

        if pch > eps:
            ch_active += 1
            sum_p_ch += pch
            e_ch = pch * DT_H
            charge_mwh += e_ch
            charge_value += pr * e_ch

        if pdis > eps:
            dis_active += 1
            sum_p_dis += pdis
            e_dis = pdis * DT_H
            discharge_mwh += e_dis
            discharge_value += pr * e_dis

    profit_day = float(m.ObjVal)
    eq_cycles = (discharge_mwh / E_MWH) if E_MWH > 0 else 0.0

    avg_charge_price = (charge_value / charge_mwh) if charge_mwh > eps else 0.0
    avg_discharge_price = (discharge_value / discharge_mwh) if discharge_mwh > eps else 0.0
    avg_ch_power_active = (sum_p_ch / ch_active) if ch_active > 0 else 0.0
    avg_dis_power_active = (sum_p_dis / dis_active) if dis_active > 0 else 0.0
    # 最后返回一个dict：包含代表日收益、代表日能量、等效循环、平均电价、平均功率、96点策略曲线
    return {
        "status": "OPTIMAL",
        "profit_day_yuan": profit_day,
        "charge_mwh_day": float(charge_mwh),
        "discharge_mwh_day": float(discharge_mwh),
        "eq_cycles_day": float(eq_cycles),

        "avg_charge_price": float(avg_charge_price),
        "avg_discharge_price": float(avg_discharge_price),
        "avg_ch_power_active_mw": float(avg_ch_power_active),
        "avg_dis_power_active_mw": float(avg_dis_power_active),

        "p_ch_mw": p_ch_list,
        "p_dis_mw": p_dis_list,

        "ch_active_intervals": int(ch_active),
        "dis_active_intervals": int(dis_active),
        "charge_value_yuan_day": float(charge_value),
        "discharge_value_yuan_day": float(discharge_value),
    }

def month_days(month_str: str) -> int:
    """month_str: 'YYYY-MM' -> days in that month"""
    y, m = month_str.split("-")
    y = int(y); m = int(m)
    return calendar.monthrange(y, m)[1]


def build_month_profile(sub: pd.DataFrame) -> pd.DataFrame:
    """
    构造当月代表性价格曲线：slot=1..96 的均价，并补齐缺点
    """
    prof = sub.groupby("slot", as_index=False).agg(price=("price", "mean"))
    full = pd.DataFrame({"slot": range(1, 97)})
    prof = full.merge(prof, on="slot", how="left")
    #ffill()用前一个 slot 的价格补,如果前面也没有，bfill()用后一个 slot 的价格补
    prof["price"] = prof["price"].ffill().bfill()
    return prof


def run_monthly(df: pd.DataFrame):
    """
    输出：
    - monthly_summary：每 node+market+month 一行（月收益+运行指标）
    - monthly_strategy：每 node+market+month 有 96 行（月策略）
    """
    df = df.copy()

    dt = pd.to_datetime(df["ts"])
    df["month"] = dt.dt.to_period("M").astype(str)  # 'YYYY-MM'
    df["slot"] = dt.dt.hour * 4 + (dt.dt.minute // 15) + 1

    groups = list(df.groupby(["node", "market", "month"], sort=True))
    print(f"即将优化：{len(groups)} 组「节点-市场-月」问题（口径：月均价策略+月均价收益）")

    monthly_rows = []
    strategy_rows = []

    for (node, market, month), sub in tqdm(groups, total=len(groups), desc="月策略优化进度"):
        # 96点代表曲线
        prof = build_month_profile(sub)
        prices96 = prof["price"].tolist()
        days = month_days(month)
        # 在“月代表日”上跑Gurobi优化
        res = optimize_profile_gurobi(prices96)

        # 口径：月收益 = 代表日收益 × 当月天数
        profit_month = res["profit_day_yuan"] * days

        # 月能量（按代表日×天数）
        total_charge_mwh = res["charge_mwh_day"] * days
        total_discharge_mwh = res["discharge_mwh_day"] * days
        sum_eq_cycles = res["eq_cycles_day"] * days

        # 利用小时（放电量/功率）
        utilization_hours = total_discharge_mwh / P_MW if P_MW > 0 else 0.0

        # 平均价差
        avg_spread = res["avg_discharge_price"] - res["avg_charge_price"]

        monthly_rows.append({
            "node": node,
            "market": market,
            "month": month,
            "days_in_month": days,
            "status": res["status"],

            # 收益
            "profit_yuan": float(profit_month),
            "profit_yuan_per_mwh_capacity": float(profit_month) / E_MWH,
            "profit_yuan_per_mw_power": float(profit_month) / P_MW,

            # 充放电次数/循环
            "eq_cycles_day": res["eq_cycles_day"],
            "sum_eq_cycles_month": float(sum_eq_cycles),
            "avg_eq_cycles_per_day": res["eq_cycles_day"],

            # 能量
            "charge_mwh_day": res["charge_mwh_day"],
            "discharge_mwh_day": res["discharge_mwh_day"],
            "total_charge_mwh_month": float(total_charge_mwh),
            "total_discharge_mwh_month": float(total_discharge_mwh),

            # 电价（能量加权，来自代表曲线）
            "avg_charge_price_yuan_per_mwh": res["avg_charge_price"],
            "avg_discharge_price_yuan_per_mwh": res["avg_discharge_price"],
            "avg_price_spread_yuan_per_mwh": float(avg_spread),

            # 功率（活跃时段平均）
            "avg_ch_power_active_mw": res["avg_ch_power_active_mw"],
            "avg_dis_power_active_mw": res["avg_dis_power_active_mw"],

            # 利用小时
            "utilization_hours_h": float(utilization_hours),
        })

        # 输出月策略 96 点
        for i in range(96):
            strategy_rows.append({
                "node": node,
                "market": market,
                "month": month,
                "slot": i + 1,
                "price_profile": float(prices96[i]),
                "p_ch_mw": float(res["p_ch_mw"][i]),
                "p_dis_mw": float(res["p_dis_mw"][i]),
            })

    monthly_summary = pd.DataFrame(monthly_rows)
    monthly_strategy = pd.DataFrame(strategy_rows)

    return monthly_summary, monthly_strategy


def make_investment_outputs_monthly(monthly_summary: pd.DataFrame, out_xlsx: str, topn: int = 10):
    """
    投决输出（月口径）：
    - TOP10_DA / TOP10_RT（按全年/全期月收益求和）
    - RT-DA 差异Top10（增益/减益）
    - 月度明细（每节点每月）
    """
    # 先按 node+market 汇总全年（月收益求和）
    total = monthly_summary.groupby(["node", "market"], as_index=False).agg(
        months=("month", "count"),
        profit_yuan=("profit_yuan", "sum"),
        avg_profit_yuan_per_month=("profit_yuan", "mean"),
        sum_eq_cycles_month=("sum_eq_cycles_month", "sum"),
        avg_eq_cycles_per_day=("avg_eq_cycles_per_day", "mean"),
        avg_charge_price_yuan_per_mwh=("avg_charge_price_yuan_per_mwh", "mean"),
        avg_discharge_price_yuan_per_mwh=("avg_discharge_price_yuan_per_mwh", "mean"),
        avg_price_spread_yuan_per_mwh=("avg_price_spread_yuan_per_mwh", "mean"),
        avg_ch_power_active_mw=("avg_ch_power_active_mw", "mean"),
        avg_dis_power_active_mw=("avg_dis_power_active_mw", "mean"),
        utilization_hours_h=("utilization_hours_h", "sum"),
        total_discharge_mwh_month=("total_discharge_mwh_month", "sum"),
        total_charge_mwh_month=("total_charge_mwh_month", "sum"),
    )
    total["profit_yuan_per_mwh_capacity"] = total["profit_yuan"] / E_MWH
    total["profit_yuan_per_mw_power"] = total["profit_yuan"] / P_MW

    da = total[total["market"] == "DA"].sort_values("profit_yuan", ascending=False).reset_index(drop=True)
    rt = total[total["market"] == "RT"].sort_values("profit_yuan", ascending=False).reset_index(drop=True)
    da["rank"] = da.index + 1
    rt["rank"] = rt.index + 1

    # 同节点对比（RT-DA）
    comp = da.merge(rt, on="node", how="outer", suffixes=("_DA", "_RT"))
    comp = comp.fillna(0)
    comp["profit_diff_RT_minus_DA"] = comp["profit_yuan_RT"] - comp["profit_yuan_DA"]
    comp["profit_ratio_RT_over_DA"] = comp["profit_yuan_RT"] / comp["profit_yuan_DA"].replace({0: pd.NA})
    comp = comp.fillna(0)

    comp_gain_top = comp.sort_values("profit_diff_RT_minus_DA", ascending=False).head(topn)
    comp_loss_top = comp.sort_values("profit_diff_RT_minus_DA", ascending=True).head(topn)

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
        da.head(topn).to_excel(w, sheet_name=f"TOP{topn}_DA", index=False)
        rt.head(topn).to_excel(w, sheet_name=f"TOP{topn}_RT", index=False)

        comp_gain_top.to_excel(w, sheet_name=f"TOP{topn}_RT-DA_增益", index=False)
        comp_loss_top.to_excel(w, sheet_name=f"TOP{topn}_RT-DA_减益", index=False)

        comp.sort_values("profit_diff_RT_minus_DA", ascending=False).to_excel(w, sheet_name="RT_vs_DA_全量", index=False)
        da.to_excel(w, sheet_name="Rank_DA_全量", index=False)
        rt.to_excel(w, sheet_name="Rank_RT_全量", index=False)

        monthly_summary.sort_values(["node", "market", "month"]).to_excel(w, sheet_name="Monthly_Summary", index=False)

    print(f"已生成投决输出Excel（月口径B）：{out_xlsx}")


def main():
    df = read_folder(DATA_DIR)

    # 月口径：一个月一套策略
    monthly_summary, monthly_strategy = run_monthly(df)

    # 输出CSV便于二次分析
    monthly_summary_csv = os.path.join(OUT_DIR, "monthly_summary.csv")
    monthly_strategy_csv = os.path.join(OUT_DIR, "monthly_strategy_96pt.csv")
    monthly_summary.to_csv(monthly_summary_csv, index=False, encoding="utf-8-sig")
    monthly_strategy.to_csv(monthly_strategy_csv, index=False, encoding="utf-8-sig")

    # 输出Excel（投决Top10 + 差异 + 月明细）
    out_xlsx = os.path.join(OUT_DIR, f"储能节点收益_TOP{TOPN}_月策略口径B_日前实时对比.xlsx")
    make_investment_outputs_monthly(monthly_summary, out_xlsx, topn=TOPN)

    # 另存：月策略96点到Excel（有时很大，单独一个文件更清爽）
    out_strategy_xlsx = os.path.join(OUT_DIR, "月策略_96点_日前实时.xlsx")
    with pd.ExcelWriter(out_strategy_xlsx, engine="openpyxl") as w:
        monthly_strategy.sort_values(["node", "market", "month", "slot"]).to_excel(w, sheet_name="Monthly_Strategy_96pt", index=False)

    print("=== DONE ===")
    print(f"- Monthly Summary CSV：{monthly_summary_csv}")
    print(f"- Monthly Strategy CSV：{monthly_strategy_csv}")
    print(f"- 投决Excel：{out_xlsx}")
    print(f"- 月策略96点Excel：{out_strategy_xlsx}")


if __name__ == "__main__":
    main()

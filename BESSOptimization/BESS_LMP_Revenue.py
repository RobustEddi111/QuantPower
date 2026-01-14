"""
储能充放电策略，日前实时混在一起
"""
import os
import re
import glob
import pandas as pd
from datetime import datetime
from tqdm import tqdm


import gurobipy as gp
from gurobipy import GRB

# ========= 你只需要改这里 =========
DATA_DIR = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\山西2025年节电电价数据"
OUT_DIR  = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\山西2025年节电电价数据储能收益测算"
# =================================
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 储能参数 ----------
P_MW = 100.0
E_MWH = 200.0
ETA_C = 0.95
ETA_D = 0.95
SOC_MIN = 0.10 * E_MWH
SOC_MAX = 0.90 * E_MWH
SOC0_FRAC = 0.50
DT_H = 0.25

# 可选：限制每日等效循环次数（0表示不启用）
MAX_EQ_CYCLES_PER_DAY = 0  # 例如 1.0 / 2.0；0=不限制


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: str(c).strip() for c in df.columns})

    def pick_col(candidates):
        for key in candidates:
            for c in df.columns:
                if key in str(c):
                    return c
        return None

    col_node = pick_col(["节点名称", "节点", "Node"])
    col_date = pick_col(["日期", "date", "Date"])
    col_time = pick_col(["时点", "时间", "Time"])
    col_price = pick_col(["节点电价", "节点电价（元/MWh）", "LMP", "price"])

    if not all([col_node, col_date, col_time, col_price]):
        raise ValueError(f"表头无法识别：node={col_node}, date={col_date}, time={col_time}, price={col_price}")

    df = df[[col_node, col_date, col_time, col_price]].copy()
    df.columns = ["node", "date", "time", "price"]

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date"])

    def parse_time(x):
        if pd.isna(x):
            return None
        if isinstance(x, (datetime, pd.Timestamp)):
            return x.time()
        s = str(x).strip()
        # Excel 时间可能是小数
        try:
            if re.fullmatch(r"\d+(\.\d+)?", s):
                frac = float(s)
                if 0 <= frac < 1:
                    total_minutes = int(round(frac * 24 * 60))
                    hh = total_minutes // 60
                    mm = total_minutes % 60
                    return datetime(2000, 1, 1, hh, mm).time()
        except:
            pass

        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).time()
            except:
                continue
        return None

    df["time"] = df["time"].apply(parse_time)
    df = df.dropna(subset=["time"])

    df["ts"] = df.apply(lambda r: datetime.combine(r["date"], r["time"]), axis=1)
    df = df.sort_values(["node", "ts"]).reset_index(drop=True)
    return df


def read_folder(data_dir: str) -> pd.DataFrame:
    import os, glob

    data_dir = data_dir.strip()

    print("DATA_DIR =", data_dir)
    print("根目录前30个条目：", os.listdir(data_dir)[:30])

    # ✅ 递归扫描：excel + csv
    patterns = ["**/*.xlsx", "**/*.xls", "**/*.xlsm", "**/*.csv"]
    files = []
    for p in patterns:
        files += glob.glob(os.path.join(data_dir, p), recursive=True)

    files = sorted(set(files))
    print(f"扫描到文件数量（含Excel/CSV）：{len(files)}")
    print("示例前5个文件：", files[:5])

    if not files:
        raise FileNotFoundError(f"未找到Excel/CSV（含子文件夹）：{data_dir}")

    all_df = []
    for fp in files:
        try:
            if fp.lower().endswith(".csv"):
                # ✅ 常见编码兜底：utf-8-sig / gbk
                try:
                    raw = pd.read_csv(fp, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    raw = pd.read_csv(fp, encoding="gbk")
            else:
                raw = pd.read_excel(fp, sheet_name=0)

            df = _normalize_columns(raw)

            # node 列全空：用文件名补上
            if df["node"].isna().all():
                df["node"] = os.path.splitext(os.path.basename(fp))[0]

            all_df.append(df)
            print(f"[OK] {os.path.basename(fp)} rows={len(df)}")

        except Exception as e:
            print(f"[SKIP] {os.path.basename(fp)} 读取失败：{e}")

    if not all_df:
        raise RuntimeError("扫描到文件但全部读取失败：检查CSV表头/分隔符/编码。")

    return pd.concat(all_df, ignore_index=True)




def optimize_one_day_gurobi(prices_mwh):
    """
    prices_mwh: list[float], 长度=96(建议)
    return: profit_yuan, charge_mwh, discharge_mwh, eq_cycles, status_str
    """
    T = len(prices_mwh)
    soc0 = SOC0_FRAC * E_MWH

    m = gp.Model("bess_arbitrage")
    m.Params.OutputFlag = 0  # 静默；调试可改 1

    # 变量
    p_ch = m.addVars(T, lb=0.0, ub=P_MW, vtype=GRB.CONTINUOUS, name="p_ch")   # MW
    p_dis = m.addVars(T, lb=0.0, ub=P_MW, vtype=GRB.CONTINUOUS, name="p_dis")# MW
    soc = m.addVars(T+1, lb=SOC_MIN, ub=SOC_MAX, vtype=GRB.CONTINUOUS, name="soc")  # MWh
    y = m.addVars(T, vtype=GRB.BINARY, name="y")  # 1=充电允许；0=放电允许（互斥）

    # 目标：Σ price*(放电-充电)*dt
    m.setObjective(gp.quicksum(prices_mwh[t] * (p_dis[t] * DT_H - p_ch[t] * DT_H) for t in range(T)),
                   GRB.MAXIMIZE)

    # SOC初值
    m.addConstr(soc[0] == soc0, name="soc_init")

    # SOC递推 + 互斥
    for t in range(T):
        m.addConstr(soc[t+1] == soc[t] + p_ch[t] * DT_H * ETA_C - p_dis[t] * DT_H / ETA_D, name=f"soc_bal_{t}")
        m.addConstr(p_ch[t] <= P_MW * y[t], name=f"ch_mutex_{t}")
        m.addConstr(p_dis[t] <= P_MW * (1 - y[t]), name=f"dis_mutex_{t}")

    # 日末闭合（投决常用）
    m.addConstr(soc[T] == soc0, name="soc_end")

    # 可选：日循环限制（等效循环≈日放电总量/E）
    if MAX_EQ_CYCLES_PER_DAY and MAX_EQ_CYCLES_PER_DAY > 0:
        m.addConstr(gp.quicksum(p_dis[t] * DT_H for t in range(T)) <= MAX_EQ_CYCLES_PER_DAY * E_MWH,
                    name="cycle_cap")

    m.optimize()

    status = m.Status
    if status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return 0.0, 0.0, 0.0, 0.0, f"STATUS_{status}"

    charge_mwh = sum(p_ch[t].X * DT_H for t in range(T))
    discharge_mwh = sum(p_dis[t].X * DT_H for t in range(T))
    profit = m.ObjVal
    eq_cycles = (discharge_mwh / E_MWH) if E_MWH > 0 else 0.0
    return float(profit), float(charge_mwh), float(discharge_mwh), float(eq_cycles), "OPTIMAL"


def run_all(df: pd.DataFrame):
    df["day"] = pd.to_datetime(df["ts"]).dt.date

    # 先把 group list 化，算清楚一共多少“节点-日”任务
    groups = list(df.groupby(["node", "day"], sort=True))
    total_tasks = len(groups)

    print(f"即将优化：{total_tasks} 个「节点-日」问题")

    results = []

    for (node, day), sub in tqdm(groups, total=total_tasks, desc="储能套利优化进度"):
        tqdm.write(f"正在计算节点：{node}，日期：{day}")
        sub = sub.sort_values("ts")
        prices = sub["price"].tolist()

        # 点数不足跳过
        if len(prices) < 90:
            continue

        profit, ch_mwh, dis_mwh, eqc, st = optimize_one_day_gurobi(prices)

        results.append({
            "node": node,
            "date": str(day),
            "n_points": len(prices),
            "profit_yuan": profit,
            "charge_mwh": ch_mwh,
            "discharge_mwh": dis_mwh,
            "eq_cycles": eqc,
            "status": st
        })

    daily = pd.DataFrame(results)
    if daily.empty:
        raise RuntimeError("未生成结果：可能数据点数不足或表头识别失败。")

    summary = daily.groupby("node", as_index=False).agg(
        days=("date", "count"),
        profit_yuan=("profit_yuan", "sum"),
        avg_profit_yuan_per_day=("profit_yuan", "mean"),
        total_charge_mwh=("charge_mwh", "sum"),
        total_discharge_mwh=("discharge_mwh", "sum"),
        avg_eq_cycles=("eq_cycles", "mean"),
        sum_eq_cycles=("eq_cycles", "sum"),
    )

    summary["profit_yuan_per_mwh_capacity"] = summary["profit_yuan"] / E_MWH
    summary["profit_yuan_per_mw_power"] = summary["profit_yuan"] / P_MW
    summary = summary.sort_values("profit_yuan", ascending=False).reset_index(drop=True)
    summary["rank"] = summary.index + 1

    return daily, summary



def main():
    df = read_folder(DATA_DIR)
    daily, summary = run_all(df)

    out_daily = os.path.join(OUT_DIR, "daily_profit_detail.csv")
    out_summary = os.path.join(OUT_DIR, "node_profit_ranking.csv")
    out_xlsx = os.path.join(OUT_DIR, "storage_profit_outputs.xlsx")

    daily.to_csv(out_daily, index=False, encoding="utf-8-sig")
    summary.to_csv(out_summary, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="node_ranking", index=False)
        daily.to_excel(w, sheet_name="daily_detail", index=False)

    print("=== DONE ===")
    print(summary.head(10))
    print(f"输出：\n- {out_xlsx}\n- {out_summary}\n- {out_daily}")


if __name__ == "__main__":
    main()

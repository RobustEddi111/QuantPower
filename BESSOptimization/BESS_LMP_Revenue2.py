
"""
BESS 节点电价套利收益测算（Gurobi版）- 投决交付（Top10 日前/实时/差异 + 关键运行指标）
功能：
1) 扫描文件夹（递归）读取 *.csv / *.xlsx / *.xls / *.xlsm
2) 从文件名识别市场：日前=DA、实时=RT，并用文件名生成 node_id（避免CSV内节点名不一致）
3) 对每个 node + market + day 做储能日内最优套利（MILP，禁止同充同放，日末SOC回到初值）
4) daily 明细输出：收益、充放电量、等效循环、能量加权充/放电价、平均充/放电功率（活跃时段）
5) 汇总报表输出：平均充放电次数、平均充/放电电价、平均充/放电功率、平均价差、等效利用小时
6) 输出投决级 Excel：
   - TOP10_DA / TOP10_RT
   - TOP10_RT-DA_增益 / TOP10_RT-DA_减益
   - RT_vs_DA_全量（同节点对比）
   - Rank_DA_全量 / Rank_RT_全量（全量排名）
   - Daily_Detail（日度明细）
7) 输出异常文件清单 bad_files.csv

依赖：
pip install pandas openpyxl gurobipy tqdm

"""

import os
import re
import glob
import pandas as pd
from datetime import datetime

import gurobipy as gp
from gurobipy import GRB
from tqdm import tqdm


# ========= 需要改这里 =========
DATA_DIR = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\山西2025年节电电价数据"
OUT_DIR  = r"D:\工作\特变电工\13项目\储能充放电节点收益分析\储能节点收益分析\山西2025年节电电价数据储能收益测算-按日分时"
# =================================
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 储能参数（按投决口径自行修改） ----------
P_MW = 100.0          # 功率 MW
E_MWH = 200.0         # 容量 MWh
ETA_C = 0.95          # 充电效率
ETA_D = 0.95          # 放电效率
SOC_MIN = 0.10 * E_MWH
SOC_MAX = 0.90 * E_MWH
SOC0_FRAC = 0.10      # 每天初始SOC占比（并要求日末回到初值）
DT_H = 0.25           # 15min=0.25h

# 可选：限制每日等效循环次数（0=不启用），例如 1.0 / 2.0
MAX_EQ_CYCLES_PER_DAY = 0

# 可选：允许一天最少点数（不足则跳过）
MIN_POINTS_PER_DAY = 90

# 输出 TopN
TOPN = 10


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """识别列：日期、时点、价格（节点电价/边际电价/LMP/电能量价）并标准化为 date/time/price/ts (+node占位)"""
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

    col_price = pick_col(["节点电价", "节点电价（元/MWh）"])
    if col_price is None:
        col_price = pick_col(["边际电价", "LMP", "节点边际电价"])
    if col_price is None:
        col_price = pick_col(["电能量价格", "电能量价", "能量价格"])

    if not all([col_date, col_time, col_price]):
        raise ValueError(f"表头无法识别：date={col_date}, time={col_time}, price={col_price}")

    use_cols = [c for c in [col_node, col_date, col_time, col_price] if c is not None]
    df = df[use_cols].copy()

    rename_map = {}
    if col_node is not None:
        rename_map[col_node] = "node"
    rename_map[col_date] = "date"
    rename_map[col_time] = "time"
    rename_map[col_price] = "price"
    df = df.rename(columns=rename_map)

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

    df["ts"] = df.apply(lambda r: datetime.combine(r["date"], r["time"]), axis=1)

    if "node" not in df.columns:
        df["node"] = None

    df = df.sort_values(["ts"]).reset_index(drop=True)
    return df


def _infer_market_and_node_from_filename(fp: str):
    """从文件名识别 market(DA/RT/UNK) 与 node_id（文件名去掉日前/实时+日期段+指标）"""
    fname = os.path.basename(fp)

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
                # 分隔符兜底：若只有一列，自动猜分隔符
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
            print(f"[OK] {fname} rows={len(df)}")

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


def optimize_one_day_gurobi(prices_mwh):
    """
    单日最优套利（MILP）：禁止同充同放，日末SOC回到初值。
    返回 dict，包含：收益、充放电量、等效循环、能量加权充/放电价、平均充/放电功率（活跃时段）
    """
    T = len(prices_mwh)
    soc0 = SOC0_FRAC * E_MWH
    eps = 1e-6

    m = gp.Model("bess_arbitrage")
    m.Params.OutputFlag = 0

    p_ch = m.addVars(T, lb=0.0, ub=P_MW, vtype=GRB.CONTINUOUS, name="p_ch")
    p_dis = m.addVars(T, lb=0.0, ub=P_MW, vtype=GRB.CONTINUOUS, name="p_dis")
    soc = m.addVars(T + 1, lb=SOC_MIN, ub=SOC_MAX, vtype=GRB.CONTINUOUS, name="soc")
    y = m.addVars(T, vtype=GRB.BINARY, name="y")

    m.setObjective(
        gp.quicksum(prices_mwh[t] * (p_dis[t] * DT_H - p_ch[t] * DT_H) for t in range(T)),
        GRB.MAXIMIZE
    )

    m.addConstr(soc[0] == soc0, name="soc_init")

    for t in range(T):
        m.addConstr(soc[t + 1] == soc[t] + p_ch[t] * DT_H * ETA_C - p_dis[t] * DT_H / ETA_D, name=f"soc_{t}")
        m.addConstr(p_ch[t] <= P_MW * y[t], name=f"mutex_ch_{t}")
        m.addConstr(p_dis[t] <= P_MW * (1 - y[t]), name=f"mutex_dis_{t}")

    m.addConstr(soc[T] == soc0, name="soc_end")

    if MAX_EQ_CYCLES_PER_DAY and MAX_EQ_CYCLES_PER_DAY > 0:
        m.addConstr(gp.quicksum(p_dis[t] * DT_H for t in range(T)) <= MAX_EQ_CYCLES_PER_DAY * E_MWH, name="cycle_cap")

    m.optimize()

    if m.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {
            "status": f"STATUS_{m.Status}",
            "profit_yuan": 0.0,
            "charge_mwh": 0.0,
            "discharge_mwh": 0.0,
            "eq_cycles": 0.0,
            "charge_value_yuan": 0.0,
            "discharge_value_yuan": 0.0,
            "avg_charge_price": 0.0,
            "avg_discharge_price": 0.0,
            "ch_active_intervals": 0,
            "dis_active_intervals": 0,
            "avg_ch_power_active_mw": 0.0,
            "avg_dis_power_active_mw": 0.0,
        }

    charge_mwh = 0.0
    discharge_mwh = 0.0
    charge_value = 0.0
    discharge_value = 0.0

    ch_active = 0
    dis_active = 0
    sum_p_ch = 0.0
    sum_p_dis = 0.0

    for t in range(T):
        pch = float(p_ch[t].X)
        pdis = float(p_dis[t].X)
        pr = float(prices_mwh[t])

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

    profit = float(m.ObjVal)
    eq_cycles = (discharge_mwh / E_MWH) if E_MWH > 0 else 0.0

    avg_charge_price = (charge_value / charge_mwh) if charge_mwh > eps else 0.0
    avg_discharge_price = (discharge_value / discharge_mwh) if discharge_mwh > eps else 0.0

    avg_ch_power_active = (sum_p_ch / ch_active) if ch_active > 0 else 0.0
    avg_dis_power_active = (sum_p_dis / dis_active) if dis_active > 0 else 0.0

    return {
        "status": "OPTIMAL",
        "profit_yuan": profit,
        "charge_mwh": float(charge_mwh),
        "discharge_mwh": float(discharge_mwh),
        "eq_cycles": float(eq_cycles),

        "charge_value_yuan": float(charge_value),
        "discharge_value_yuan": float(discharge_value),
        "avg_charge_price": float(avg_charge_price),
        "avg_discharge_price": float(avg_discharge_price),

        "ch_active_intervals": int(ch_active),
        "dis_active_intervals": int(dis_active),
        "avg_ch_power_active_mw": float(avg_ch_power_active),
        "avg_dis_power_active_mw": float(avg_dis_power_active),
    }


def run_all(df: pd.DataFrame) -> pd.DataFrame:
    """按 node + market + day 逐日优化，返回 daily 明细表"""
    df = df.copy()
    df["day"] = pd.to_datetime(df["ts"]).dt.date

    print("总行数=", len(df))
    print("节点数=", df["node"].nunique(), "市场数=", df["market"].nunique(), "天数(全局)=", df["day"].nunique())

    groups = list(df.groupby(["node", "market", "day"], sort=True))
    print(f"即将优化：{len(groups)} 个「节点-市场-日」问题")

    results = []
    for (node, market, day), sub in tqdm(groups, total=len(groups), desc="储能套利优化进度"):
        sub = sub.sort_values("ts")
        prices = sub["price"].tolist()

        if len(prices) < MIN_POINTS_PER_DAY:
            continue

        res = optimize_one_day_gurobi(prices)

        results.append({
            "node": node,
            "market": market,
            "date": str(day),
            "n_points": len(prices),

            "profit_yuan": res["profit_yuan"],
            "charge_mwh": res["charge_mwh"],
            "discharge_mwh": res["discharge_mwh"],
            "eq_cycles": res["eq_cycles"],
            "status": res["status"],

            "charge_value_yuan": res["charge_value_yuan"],
            "discharge_value_yuan": res["discharge_value_yuan"],
            "avg_charge_price": res["avg_charge_price"],
            "avg_discharge_price": res["avg_discharge_price"],

            "ch_active_intervals": res["ch_active_intervals"],
            "dis_active_intervals": res["dis_active_intervals"],
            "avg_ch_power_active_mw": res["avg_ch_power_active_mw"],
            "avg_dis_power_active_mw": res["avg_dis_power_active_mw"],
        })

    daily = pd.DataFrame(results)
    if daily.empty:
        raise RuntimeError("未生成任何优化结果：检查是否点数不足/表头识别失败。")

    return daily


def make_investment_outputs(daily: pd.DataFrame, out_xlsx: str, topn: int = 10):
    """生成投决交付级Excel：Top10 日前/实时/差异 + 全量排名 + 日度明细，并加入关键运行指标"""

    def build_summary(df_part: pd.DataFrame, market: str):
        d = df_part[df_part["market"] == market].copy()

        s = d.groupby("node", as_index=False).agg(
            days=("date", "count"),
            profit_yuan=("profit_yuan", "sum"),

            total_charge_mwh=("charge_mwh", "sum"),
            total_discharge_mwh=("discharge_mwh", "sum"),

            # 等效循环（充放电次数口径）
            sum_eq_cycles=("eq_cycles", "sum"),
            avg_eq_cycles_per_day=("eq_cycles", "mean"),

            # 金额（用于能量加权平均电价）
            total_charge_value_yuan=("charge_value_yuan", "sum"),
            total_discharge_value_yuan=("discharge_value_yuan", "sum"),

            # 活跃时段数（用于时段加权平均功率）
            ch_active_intervals=("ch_active_intervals", "sum"),
            dis_active_intervals=("dis_active_intervals", "sum"),
        )

        # 能量加权平均电价
        s["avg_charge_price_yuan_per_mwh"] = s["total_charge_value_yuan"] / s["total_charge_mwh"].replace({0: pd.NA})
        s["avg_discharge_price_yuan_per_mwh"] = s["total_discharge_value_yuan"] / s["total_discharge_mwh"].replace({0: pd.NA})

        # 时段加权平均功率（仅在发生充/放电的时段）
        s["avg_ch_power_active_mw"] = s["total_charge_mwh"] / (DT_H * s["ch_active_intervals"].replace({0: pd.NA}))
        s["avg_dis_power_active_mw"] = s["total_discharge_mwh"] / (DT_H * s["dis_active_intervals"].replace({0: pd.NA}))

        # 平均价差（能量加权口径）
        s["avg_price_spread_yuan_per_mwh"] = s["avg_discharge_price_yuan_per_mwh"] - s["avg_charge_price_yuan_per_mwh"]

        # 等效利用小时（放电量/功率）
        s["utilization_hours_h"] = s["total_discharge_mwh"] / P_MW

        # 辅助理解：平均日放电量
        s["avg_discharge_mwh_per_day"] = s["total_discharge_mwh"] / s["days"].replace({0: pd.NA})

        s["market"] = market
        s = s.sort_values("profit_yuan", ascending=False).reset_index(drop=True)
        s["rank"] = s.index + 1

        # 单位收益（投决常用）
        s["profit_yuan_per_mwh_capacity"] = s["profit_yuan"] / E_MWH
        s["profit_yuan_per_mw_power"] = s["profit_yuan"] / P_MW

        # NA填0便于展示（可选）
        s = s.fillna(0)
        return s

    summary_da = build_summary(daily, "DA")
    summary_rt = build_summary(daily, "RT")

    # 同节点对比（RT-DA）
    comp = summary_da.merge(
        summary_rt,
        on="node",
        how="outer",
        suffixes=("_DA", "_RT")
    )

    # 关键对比：收益差
    comp["profit_diff_RT_minus_DA"] = comp["profit_yuan_RT"] - comp["profit_yuan_DA"]
    comp["profit_ratio_RT_over_DA"] = comp["profit_yuan_RT"] / comp["profit_yuan_DA"].replace({0: pd.NA})
    comp = comp.fillna(0)

    comp_gain_top = comp.sort_values("profit_diff_RT_minus_DA", ascending=False).head(topn)
    comp_loss_top = comp.sort_values("profit_diff_RT_minus_DA", ascending=True).head(topn)

    top_da = summary_da.head(topn)
    top_rt = summary_rt.head(topn)

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
        # Top10
        top_da.to_excel(w, sheet_name=f"TOP{topn}_DA", index=False)
        top_rt.to_excel(w, sheet_name=f"TOP{topn}_RT", index=False)

        # 差异Top10
        comp_gain_top.to_excel(w, sheet_name=f"TOP{topn}_RT-DA_增益", index=False)
        comp_loss_top.to_excel(w, sheet_name=f"TOP{topn}_RT-DA_减益", index=False)

        # 全量对比与排名
        comp.sort_values("profit_diff_RT_minus_DA", ascending=False).to_excel(w, sheet_name="RT_vs_DA_全量", index=False)
        summary_da.to_excel(w, sheet_name="Rank_DA_全量", index=False)
        summary_rt.to_excel(w, sheet_name="Rank_RT_全量", index=False)

        # 日度明细
        daily.to_excel(w, sheet_name="Daily_Detail", index=False)

    print(f"已生成投决输出Excel：{out_xlsx}")


def main():
    df = read_folder(DATA_DIR)
    daily = run_all(df)

    # 也输出 csv 便于二次分析
    daily_csv = os.path.join(OUT_DIR, "daily_profit_detail.csv")
    daily.to_csv(daily_csv, index=False, encoding="utf-8-sig")

    out_xlsx = os.path.join(OUT_DIR, f"储能节点收益_TOP{TOPN}_日前实时对比_含运行指标.xlsx")
    make_investment_outputs(daily, out_xlsx, topn=TOPN)

    print("=== DONE ===")
    print(f"- 日度明细CSV：{daily_csv}")
    print(f"- 投决Excel：{out_xlsx}")


if __name__ == "__main__":
    main()

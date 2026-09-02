#!/usr/bin/env python3
"""
FF5 + WML 확장 (Fama-French 2015 표준)
- OP = (revt - cogs - xsga - xint) / ceq  (직전 회계연도)
- INV = at_{t-1} / at_{t-2} - 1
- 6월 말 3개의 2x3 소트 (Size×B/M, Size×OP, Size×INV), KOSPI 브레이크포인트
- SMB = 3개 소트 SMB 평균 / HML, RMW, CMA 표준 정의 / WML 기존 유지
- 패널: 상폐 -30% 조정본 (공식)
산출: factors_monthly_kr_ff5.csv (MKT_RF, SMB, HML, RMW, CMA, WML, RF, MKT)
"""
import warnings, sys, os
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_factors import build_panel, pull_rf
OUT = os.environ.get("KFF_OUT", os.path.dirname(os.path.abspath(__file__)))

MERGER_CODES = {"01", "04"}

def delist_adjust(panel, dl, dlret=-0.30):
    last = panel.groupby("gvkey").agg(last_month=("month", "max"), last_me=("me", "last"),
                                      exchg=("exchg", "last")).reset_index()
    dlx = dl[~dl.dlrsni.isin(MERGER_CODES)].copy()
    dlx["dl_month"] = dlx["dldtei"].dt.to_period("M")
    dlx = dlx.sort_values("dldtei").drop_duplicates("gvkey", keep="last")
    m = last.merge(dlx[["gvkey", "dl_month"]], on="gvkey", how="inner")
    gap = (m["dl_month"] - m["last_month"]).apply(lambda x: x.n)
    m = m[(gap >= 0) & (gap <= 6)]
    add = pd.DataFrame({"gvkey": m["gvkey"], "month": m["last_month"] + 1, "exchg": m["exchg"],
                        "me": m["last_me"] * (1 + dlret), "prev_me": m["last_me"], "ret": dlret})
    return pd.concat([panel, add], ignore_index=True)

def prep_fundamentals(fund):
    f = fund.copy()
    for c in ["ceq", "revt", "cogs", "xsga", "xint", "at"]:
        f[c] = pd.to_numeric(f[c], errors="coerce").astype("float64")
    f["fy_end_year"] = f["datadate"].dt.year
    f = f.sort_values("datadate").drop_duplicates(["gvkey", "fy_end_year"], keep="last")
    f["xint"] = f["xint"].fillna(0)
    f["op_num"] = f["revt"] - f["cogs"] - f["xsga"] - f["xint"]
    f["op"] = np.where(f["ceq"] > 0, f["op_num"] / f["ceq"], np.nan)
    f = f.sort_values(["gvkey", "fy_end_year"])
    f["at_prev"] = f.groupby("gvkey")["at"].shift(1)
    f["fy_gap"] = f.groupby("gvkey")["fy_end_year"].diff()
    f["inv"] = np.where((f["fy_gap"] == 1) & (f["at_prev"] > 0), f["at"] / f["at_prev"] - 1, np.nan)
    return f.set_index(["gvkey", "fy_end_year"])

def annual_sorts_ff5(panel, f):
    be = f["ceq"]; op = f["op"]; inv = f["inv"]
    dec = panel[panel["month"].dt.month == 12]
    dec_me = dec.set_index(["gvkey", dec["month"].dt.year])["me"]

    rows = []
    for y in range(2001, panel["month"].dt.year.max() + 1):
        jun = panel[(panel["month"].dt.year == y) & (panel["month"].dt.month == 6)][
            ["gvkey", "exchg", "me"]].dropna()
        if len(jun) < 100:
            continue
        jun["be"] = jun["gvkey"].map(lambda g: be.get((g, y - 1), np.nan))
        jun["dec_me"] = jun["gvkey"].map(lambda g: dec_me.get((g, y - 1), np.nan))
        jun["bm"] = jun["be"] / jun["dec_me"]
        jun["op"] = jun["gvkey"].map(lambda g: op.get((g, y - 1), np.nan))
        jun["inv"] = jun["gvkey"].map(lambda g: inv.get((g, y - 1), np.nan))

        kospi = jun[jun["exchg"] == 248]
        size_bp = kospi["me"].median()
        jun["size_p"] = np.where(jun["me"] <= size_bp, "S", "B")

        def bp3(series_kospi, series_all, lo_lab, hi_lab, valid=None):
            v = series_kospi.dropna()
            lo, hi = v.quantile(0.3), v.quantile(0.7)
            out = np.select([series_all <= lo, series_all >= hi], [lo_lab, hi_lab], "N")
            return np.where(series_all.notna() if valid is None else valid, out, None)

        jun["bm_p"] = bp3(kospi[kospi["bm"] > 0]["bm"], jun["bm"], "G", "V", valid=(jun["bm"] > 0))
        jun["op_p"] = bp3(kospi["op"], jun["op"], "W", "R")
        jun["inv_p"] = bp3(kospi["inv"], jun["inv"], "C", "A")
        jun["form_year"] = y
        rows.append(jun[["gvkey", "form_year", "size_p", "bm_p", "op_p", "inv_p"]])
    return pd.concat(rows)

def compute_ff5(panel, assign, rf):
    p = panel.dropna(subset=["ret", "prev_me"]).copy()
    ym = p["month"]
    p["form_year"] = np.where(ym.dt.month >= 7, ym.dt.year, ym.dt.year - 1)
    p = p.merge(assign, on=["gvkey", "form_year"], how="left")

    def vw(df):
        return np.average(df["ret"], weights=df["prev_me"])

    out = []
    for month, mdf in p.groupby("month"):
        row = {"month": month, "mkt": vw(mdf)}
        smbs = []
        for char, hi, lo, fname in [("bm_p", "V", "G", "hml"), ("op_p", "R", "W", "rmw"), ("inv_p", "C", "A", "cma")]:
            six = mdf.dropna(subset=["size_p", char])
            if six.groupby(["size_p", char]).ngroups == 6:
                pr = six.groupby(["size_p", char]).apply(vw)
                row[fname] = (pr[("S", hi)] + pr[("B", hi)]) / 2 - (pr[("S", lo)] + pr[("B", lo)]) / 2
                smbs.append(pr.loc["S"].mean() - pr.loc["B"].mean())
        if smbs:
            row["smb"] = np.mean(smbs)
        out.append(row)
    fac = pd.DataFrame(out).set_index("month").sort_index()
    fac = fac.join(rf.set_index("month"))
    fac["mkt_rf"] = fac["mkt"] - fac["rf"]
    return fac

if __name__ == "__main__":
    _raw = [f"{OUT}/raw_secd.parquet", f"{OUT}/raw_funda_full.parquet", f"{OUT}/raw_delist.parquet"]
    if "--refresh" in sys.argv or not all(os.path.exists(p) for p in _raw):
        from build_factors import pull_ff5_raw
        pull_ff5_raw()
    sec = pd.read_parquet(f"{OUT}/raw_secd.parquet")
    fund = pd.read_parquet(f"{OUT}/raw_funda_full.parquet")
    dl = pd.read_parquet(f"{OUT}/raw_delist.parquet")
    rf = pull_rf()

    panel = delist_adjust(build_panel(sec), dl, -0.30)
    f = prep_fundamentals(fund)
    assign = annual_sorts_ff5(panel, f)
    fac = compute_ff5(panel, assign, rf)

    # WML: 기존 조정본에서 가져옴 (동일 패널 기반 재계산)
    from build_factors import compute_factors, annual_sorts
    old_assign = annual_sorts(panel, fund.rename(columns={"ceq": "ceq"})[["gvkey", "datadate", "fyear", "ceq"]])
    old = compute_factors(panel, old_assign, rf)
    fac = fac.join((old[["WML"]] / 100).rename(columns={"WML": "wml"}))

    # 실데이터 마지막 월에서 절단 (상폐 의사 행만 있는 꼬리 월 제거)
    real_max = build_panel(sec)["month"].max()
    fac = fac.loc["2001-07":real_max]
    result = (fac[["mkt_rf", "smb", "hml", "rmw", "cma", "wml", "rf", "mkt"]] * 100).round(4)
    result.columns = ["MKT_RF", "SMB", "HML", "RMW", "CMA", "WML", "RF", "MKT"]
    result.to_csv(f"{OUT}/factors_monthly_kr_ff5.csv")
    print(f"saved: factors_monthly_kr_ff5.csv ({len(result)} months)")
    print(result.describe().loc[["count", "mean", "std"]].round(3).to_string())

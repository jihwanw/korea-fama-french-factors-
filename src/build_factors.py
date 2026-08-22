#!/usr/bin/env python3
"""
한국 주식시장 Fama-French 팩터 구축 (Phase 1: MKT-RF, SMB, HML, WML)
METHODOLOGY.md v1.0 구현
- 데이터: WRDS Compustat Global (g_secd monthend, g_funda) + ECOS CD91
- 산출: factors_monthly_kr.csv
"""
import os, sys, json, warnings, configparser, builtins, getpass, urllib.request
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
OUT = os.environ.get("KFF_OUT", os.path.dirname(os.path.abspath(__file__)))

# ---------- 0. 자격증명 ----------
cfg = configparser.ConfigParser()
cfg.read(os.environ.get("KFF_CREDS", "/Users/jihwanw/PhD/code/api_info/api_keys.ini"))
WRDS_U, WRDS_P = cfg.get("wrds", "username"), cfg.get("wrds", "password")
ECOS_KEY = cfg.get("ecos", "api_key", fallback=None) or cfg.get("ecos", "key")

# ---------- 1. WRDS 데이터 수집 ----------
def wrds_conn():
    os.environ["PGPASSWORD"] = WRDS_P
    builtins.input = lambda p="": WRDS_U
    getpass.getpass = lambda p="": WRDS_P
    import wrds
    return wrds.Connection(wrds_username=WRDS_U)

def pull_data():
    conn = wrds_conn()
    print("[1/3] g_secd 월말 데이터 수집 (KOSPI 248, KOSDAQ 298)...")
    sec = conn.raw_sql("""
        SELECT gvkey, iid, datadate, exchg, prccd, ajexdi, trfd, cshoc
        FROM comp_global_daily.g_secd
        WHERE fic='KOR' AND curcdd='KRW' AND tpci='0'
          AND exchg IN (248, 298) AND monthend=1
          AND prccd > 0 AND cshoc > 0 AND ajexdi > 0
    """, date_cols=["datadate"])
    print(f"    {len(sec):,} rows, {sec.gvkey.nunique():,} firms")

    print("[2/3] g_funda 재무제표 (ceq)...")
    fund = conn.raw_sql("""
        SELECT gvkey, datadate, fyear, ceq
        FROM comp_global_daily.g_funda
        WHERE fic='KOR' AND ceq IS NOT NULL
          AND indfmt='INDL' AND datafmt='HIST_STD' AND consol='C' AND popsrc='I'
    """, date_cols=["datadate"])
    print(f"    {len(fund):,} rows, {fund.gvkey.nunique():,} firms")
    conn.close()
    sec.to_parquet(f"{OUT}/raw_secd.parquet")
    fund.to_parquet(f"{OUT}/raw_funda.parquet")
    return sec, fund

def pull_rf():
    print("[3/3] ECOS CD91 월별...")
    url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/1/1000/"
           f"721Y001/M/199103/202612/2010000")
    data = json.loads(urllib.request.urlopen(url, timeout=30).read())
    rows = data["StatisticSearch"]["row"]
    rf = pd.DataFrame([(r["TIME"], float(r["DATA_VALUE"])) for r in rows],
                      columns=["ym", "cd91_pct"])
    rf["month"] = pd.to_datetime(rf["ym"], format="%Y%m").dt.to_period("M")
    rf["rf"] = (1 + rf["cd91_pct"] / 100) ** (1 / 12) - 1
    print(f"    {len(rf)} months ({rf.ym.min()}~{rf.ym.max()})")
    return rf[["month", "rf"]]

# ---------- 2. 월간 수익률·ME 패널 ----------
def build_panel(sec):
    sec = sec.copy()
    sec["month"] = sec["datadate"].dt.to_period("M")
    sec["trfd"] = sec["trfd"].fillna(1.0)
    sec["adjprc"] = sec["prccd"] / sec["ajexdi"] * sec["trfd"]
    sec["me"] = sec["prccd"] * sec["cshoc"]

    # gvkey당 복수 발행(iid) → 월별 최대 ME 발행만
    sec = sec.sort_values("me").drop_duplicates(["gvkey", "month"], keep="last")
    sec = sec.sort_values(["gvkey", "month"]).reset_index(drop=True)

    # 연속 월말 수익률
    g = sec.groupby("gvkey")
    sec["prev_month"] = g["month"].shift(1)
    sec["prev_adjprc"] = g["adjprc"].shift(1)
    sec["prev_me"] = g["me"].shift(1)
    consec = (sec["month"] - sec["prev_month"]).apply(lambda x: x.n if pd.notna(x) else 99) == 1
    sec["ret"] = np.where(consec, sec["adjprc"] / sec["prev_adjprc"] - 1, np.nan)
    # 극단 이상치 방어 (데이터 오류: ±300% 초과 월간수익률 제거)
    sec.loc[sec["ret"].abs() > 3, "ret"] = np.nan
    return sec[["gvkey", "month", "exchg", "me", "prev_me", "ret"]]

# ---------- 3. 6월 리밸런싱 소트 (Size × B/M) ----------
def annual_sorts(panel, fund):
    fund = fund.copy()
    fund["fy_end_year"] = fund["datadate"].dt.year
    # 회계연도 중복 시 최신 datadate
    fund = fund.sort_values("datadate").drop_duplicates(["gvkey", "fy_end_year"], keep="last")
    be = fund.set_index(["gvkey", "fy_end_year"])["ceq"]

    dec_me = panel[panel["month"].dt.month == 12].set_index(
        ["gvkey", panel[panel["month"].dt.month == 12]["month"].dt.year])["me"]

    assignments = []
    years = range(2001, panel["month"].dt.year.max() + 1)
    for y in years:
        jun = panel[(panel["month"].dt.year == y) & (panel["month"].dt.month == 6)][
            ["gvkey", "exchg", "me"]].dropna()
        if len(jun) < 100:
            continue
        # B/M: BE(FY ending in y-1) / ME(Dec y-1)
        jun["be"] = jun["gvkey"].map(lambda g: be.get((g, y - 1), np.nan))
        jun["dec_me"] = jun["gvkey"].map(lambda g: dec_me.get((g, y - 1), np.nan))
        jun["bm"] = jun["be"] / jun["dec_me"]

        kospi = jun[jun["exchg"] == 248]
        size_bp = kospi["me"].median()
        bm_valid = kospi[kospi["bm"] > 0]["bm"]
        bm30, bm70 = bm_valid.quantile(0.3), bm_valid.quantile(0.7)

        jun["size_p"] = np.where(jun["me"] <= size_bp, "S", "B")
        jun["bm_p"] = np.select(
            [jun["bm"] <= bm30, jun["bm"] >= bm70], ["G", "V"], "N")
        jun.loc[~(jun["bm"] > 0), "bm_p"] = None  # BE<=0 또는 결측 제외
        jun["form_year"] = y
        assignments.append(jun[["gvkey", "form_year", "size_p", "bm_p"]])
    return pd.concat(assignments)

# ---------- 4. 팩터 계산 ----------
def compute_factors(panel, assign, rf):
    p = panel.dropna(subset=["ret", "prev_me"]).copy()
    ym = p["month"]
    # 보유기간: 7월(y)~6월(y+1) → form_year 매핑
    p["form_year"] = np.where(ym.dt.month >= 7, ym.dt.year, ym.dt.year - 1)
    p = p.merge(assign, on=["gvkey", "form_year"], how="left")

    def vw(df):
        return np.average(df["ret"], weights=df["prev_me"])

    out = []
    for month, mdf in p.groupby("month"):
        row = {"month": month}
        row["mkt"] = vw(mdf)
        six = mdf.dropna(subset=["size_p", "bm_p"])
        if six.groupby(["size_p", "bm_p"]).ngroups == 6:
            pr = six.groupby(["size_p", "bm_p"]).apply(vw)
            row["smb"] = pr.loc["S"].mean() - pr.loc["B"].mean()
            row["hml"] = (pr[("S", "V")] + pr[("B", "V")]) / 2 - (pr[("S", "G")] + pr[("B", "G")]) / 2
        out.append(row)
    fac = pd.DataFrame(out).set_index("month").sort_index()

    # WML: 매월, 12-2 모멘텀 (최소 8개월 유효)
    p2 = panel.sort_values(["gvkey", "month"]).copy()
    p2["logret"] = np.log1p(p2["ret"])
    mom_rows = []
    pivot_ret = p2.pivot(index="month", columns="gvkey", values="logret")
    pivot_me = p2.pivot(index="month", columns="gvkey", values="me")
    pivot_ex = p2.pivot(index="month", columns="gvkey", values="exchg")
    months = pivot_ret.index.sort_values()
    cum = pivot_ret.rolling(11, min_periods=8).sum().shift(2)  # t-12 ~ t-2
    for i, m in enumerate(months):
        if m.year < 2001 or (m.year == 2001 and m.month < 7):
            continue
        mom = cum.loc[m].dropna()
        prev_m = months[i - 1] if i > 0 else None
        if prev_m is None:
            continue
        me_prev = pivot_me.loc[prev_m]
        ret_now = np.expm1(pivot_ret.loc[m])
        ex_prev = pivot_ex.loc[prev_m]
        df = pd.DataFrame({"mom": mom, "me": me_prev, "ret": ret_now, "exchg": ex_prev}).dropna()
        if len(df) < 100:
            continue
        kospi = df[df["exchg"] == 248]
        m30, m70 = kospi["mom"].quantile(0.3), kospi["mom"].quantile(0.7)
        size_bp = kospi["me"].median()
        df["sp"] = np.where(df["me"] <= size_bp, "S", "B")
        df["mp"] = np.select([df["mom"] <= m30, df["mom"] >= m70], ["L", "W"], "M")
        pr = df.groupby(["sp", "mp"]).apply(lambda d: np.average(d["ret"], weights=d["me"]))
        try:
            wml = (pr[("S", "W")] + pr[("B", "W")]) / 2 - (pr[("S", "L")] + pr[("B", "L")]) / 2
            mom_rows.append({"month": m, "wml": wml})
        except KeyError:
            pass
    wml = pd.DataFrame(mom_rows).set_index("month")

    fac = fac.join(wml).join(rf.set_index("month"))
    fac["mkt_rf"] = fac["mkt"] - fac["rf"]
    fac = fac.loc["2001-07":]
    result = (fac[["mkt_rf", "smb", "hml", "wml", "rf", "mkt"]] * 100).round(4)
    result.columns = ["MKT_RF", "SMB", "HML", "WML", "RF", "MKT"]
    return result

if __name__ == "__main__":
    if os.path.exists(f"{OUT}/raw_secd.parquet") and "--refresh" not in sys.argv:
        sec = pd.read_parquet(f"{OUT}/raw_secd.parquet")
        fund = pd.read_parquet(f"{OUT}/raw_funda.parquet")
        print("cached raw data loaded")
    else:
        sec, fund = pull_data()
    rf = pull_rf()
    print("패널 구축...")
    panel = build_panel(sec)
    print(f"    {len(panel):,} firm-months")
    print("연간 소트...")
    assign = annual_sorts(panel, fund)
    print("팩터 계산...")
    factors = compute_factors(panel, assign, rf)
    factors.to_csv(f"{OUT}/factors_monthly_kr.csv")
    print(f"\n저장: factors_monthly_kr.csv ({len(factors)} months)")
    print(factors.describe().round(3).to_string())

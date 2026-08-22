#!/usr/bin/env python3
"""
구현 증명: 동일 소트/공식 로직을 CRSP/Compustat(미국)에 적용해
Fama-French 공식 팩터(ff.fivefactors_monthly)를 재현.
표본: 1995-07 ~ 2024-12. 기대: MKT 0.99+, SMB/HML 0.95+, RMW/CMA 0.93+
"""
import os, configparser, builtins, getpass, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
cfg = configparser.ConfigParser(); cfg.read("/Users/jihwanw/PhD/code/api_info/api_keys.ini")
u, pw = cfg.get("wrds","username"), cfg.get("wrds","password")
os.environ["PGPASSWORD"] = pw
builtins.input = lambda p="": u
getpass.getpass = lambda p="": pw
import wrds

def pull():
    conn = wrds.Connection(wrds_username=u)
    print("[1/5] CRSP monthly (1993-2024, 보통주, NYSE/AMEX/NASDAQ)...")
    crsp = conn.raw_sql("""
        SELECT m.permno, m.date, m.ret, m.prc, m.shrout, n.exchcd
        FROM crsp.msf m
        JOIN crsp.msenames n ON m.permno=n.permno
          AND m.date BETWEEN n.namedt AND n.nameendt
        WHERE m.date BETWEEN '1993-01-01' AND '2024-12-31'
          AND n.shrcd IN (10,11) AND n.exchcd IN (1,2,3)
    """, date_cols=["date"])
    print(f"    {len(crsp):,} rows")
    print("[2/5] delisting returns...")
    dl = conn.raw_sql("SELECT permno, dlstdt, dlret FROM crsp.msedelist", date_cols=["dlstdt"])
    print("[3/5] Compustat funda...")
    fund = conn.raw_sql("""
        SELECT gvkey, datadate, fyear, seq, ceq, pstk, pstkrv, pstkl, txditc,
               revt, cogs, xsga, xint, at
        FROM comp.funda
        WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
          AND datadate BETWEEN '1992-01-01' AND '2024-12-31'
    """, date_cols=["datadate"])
    print(f"    {len(fund):,} rows")
    print("[4/5] CUSIP 기반 링크 (CCM 권한 부재 → 표준 대안)...")
    link = conn.raw_sql("""
        SELECT DISTINCT n.permno, s.gvkey, n.namedt, n.nameendt
        FROM crsp.msenames n
        JOIN comp.security s ON n.ncusip = SUBSTR(s.cusip, 1, 8)
        WHERE n.ncusip IS NOT NULL AND s.cusip IS NOT NULL
    """, date_cols=["namedt","nameendt"])
    print(f"    {len(link):,} link rows, {link.permno.nunique():,} permnos")
    print("[5/5] French 공식 팩터...")
    ff = conn.raw_sql("SELECT date, mktrf, smb, hml, rmw, cma FROM ff.fivefactors_monthly WHERE date>='1995-01-01'", date_cols=["date"])
    conn.close()
    return crsp, dl, fund, link, ff

def build_us_panel(crsp, dl):
    c = crsp.copy()
    for col in ["ret","prc","shrout"]:
        c[col] = pd.to_numeric(c[col], errors="coerce").astype("float64")
    c["month"] = c["date"].dt.to_period("M")
    c["me"] = c["prc"].abs() * c["shrout"]
    # 상폐 수익률 결합 (CRSP 표준)
    dl = dl.copy(); dl["month"] = dl["dlstdt"].dt.to_period("M")
    dl["dlret"] = pd.to_numeric(dl["dlret"], errors="coerce")
    c = c.merge(dl[["permno","month","dlret"]], on=["permno","month"], how="left")
    c["ret"] = np.where(c["dlret"].notna(),
                        (1+c["ret"].fillna(0))*(1+c["dlret"])-1, c["ret"])
    c = c.sort_values(["permno","month"])
    g = c.groupby("permno")
    c["prev_me"] = g["me"].shift(1)
    c["prev_month"] = g["month"].shift(1)
    ok = (c["month"] - c["prev_month"]).apply(lambda x: x.n if pd.notna(x) else 99) == 1
    c.loc[~ok, "prev_me"] = np.nan
    return c[["permno","month","exchcd","me","prev_me","ret"]]

def prep_be(fund):
    f = fund.copy()
    for col in f.columns.drop(["gvkey","datadate"]):
        f[col] = pd.to_numeric(f[col], errors="coerce").astype("float64")
    ps = f["pstkrv"].fillna(f["pstkl"]).fillna(f["pstk"]).fillna(0)
    se = f["seq"].fillna(f["ceq"] + f["pstk"].fillna(0))
    f["be"] = se + f["txditc"].fillna(0) - ps
    f["xint0"] = f["xint"].fillna(0)
    cost = f["cogs"].fillna(0) + f["xsga"].fillna(0) + f["xint0"]
    has_cost = f[["cogs","xsga","xint"]].notna().any(axis=1)
    f["op"] = np.where((f["be"] > 0) & f["revt"].notna() & has_cost,
                       (f["revt"] - cost) / f["be"], np.nan)
    f["fy_end_year"] = f["datadate"].dt.year
    f = f.sort_values("datadate").drop_duplicates(["gvkey","fy_end_year"], keep="last")
    f = f.sort_values(["gvkey","fy_end_year"])
    f["at_prev"] = f.groupby("gvkey")["at"].shift(1)
    f["fy_gap"] = f.groupby("gvkey")["fy_end_year"].diff()
    f["inv"] = np.where((f["fy_gap"]==1) & (f["at_prev"]>0), f["at"]/f["at_prev"]-1, np.nan)
    return f[["gvkey","fy_end_year","be","op","inv"]]

def link_gvkey(panel_jun, link, year):
    jd = pd.Timestamp(f"{year}-06-30")
    lk = link[(link["namedt"] <= jd) & (link["nameendt"].isna() | (link["nameendt"] >= jd))]
    return panel_jun.merge(lk[["gvkey","permno"]].drop_duplicates("permno"), on="permno", how="left")

def annual_sorts_us(panel, f, link):
    fidx = f.set_index(["gvkey","fy_end_year"])
    dec = panel[panel["month"].dt.month == 12]
    dec_me = dec.set_index(["permno", dec["month"].dt.year])["me"]
    rows = []
    for y in range(1995, 2025):
        jun = panel[(panel["month"].dt.year==y) & (panel["month"].dt.month==6)][
            ["permno","exchcd","me"]].dropna()
        jun = link_gvkey(jun, link, y).dropna(subset=["gvkey"])
        jun["be"]  = [fidx["be"].get((g, y-1), np.nan)  for g in jun["gvkey"]]
        jun["op"]  = [fidx["op"].get((g, y-1), np.nan)  for g in jun["gvkey"]]
        jun["inv"] = [fidx["inv"].get((g, y-1), np.nan) for g in jun["gvkey"]]
        jun["dec_me"] = [dec_me.get((p, y-1), np.nan) for p in jun["permno"]]
        jun["bm"] = jun["be"] / jun["dec_me"]
        ny = jun[jun["exchcd"]==1]
        size_bp = ny["me"].median()
        jun["size_p"] = np.where(jun["me"]<=size_bp, "S", "B")
        def bp3(k, a, lo_lab, hi_lab, valid):
            v = k.dropna(); lo, hi = v.quantile(.3), v.quantile(.7)
            out = np.select([a<=lo, a>=hi],[lo_lab,hi_lab],"N")
            return np.where(valid, out, None)
        jun["bm_p"]  = bp3(ny[ny["bm"]>0]["bm"], jun["bm"], "G","V", (jun["bm"]>0))
        jun["op_p"]  = bp3(ny["op"],  jun["op"],  "W","R", jun["op"].notna())
        jun["inv_p"] = bp3(ny["inv"], jun["inv"], "C","A", jun["inv"].notna())
        jun["form_year"] = y
        rows.append(jun[["permno","form_year","size_p","bm_p","op_p","inv_p"]])
    return pd.concat(rows)

def compute(panel, assign):
    p = panel.dropna(subset=["ret","prev_me"]).copy()
    ym = p["month"]
    p["form_year"] = np.where(ym.dt.month>=7, ym.dt.year, ym.dt.year-1)
    p = p.merge(assign, on=["permno","form_year"], how="left")
    def vw(d): return np.average(d["ret"], weights=d["prev_me"])
    out = []
    for month, mdf in p.groupby("month"):
        row = {"month": month, "mkt": vw(mdf)}
        smbs = []
        for char, hi, lo, name in [("bm_p","V","G","hml"),("op_p","R","W","rmw"),("inv_p","C","A","cma")]:
            six = mdf.dropna(subset=["size_p",char])
            if six.groupby(["size_p",char]).ngroups==6:
                pr = six.groupby(["size_p",char]).apply(vw)
                row[name] = (pr[("S",hi)]+pr[("B",hi)])/2 - (pr[("S",lo)]+pr[("B",lo)])/2
                smbs.append(pr.loc["S"].mean()-pr.loc["B"].mean())
        if smbs: row["smb"] = np.mean(smbs)
        out.append(row)
    return pd.DataFrame(out).set_index("month").sort_index().loc["1995-07":]

if __name__ == "__main__":
    cache = f"{OUT}/us_cache.pkl"
    if os.path.exists(cache):
        import pickle
        crsp, dl, fund, link, ff = pickle.load(open(cache,"rb"))
        print("cache loaded")
    else:
        crsp, dl, fund, link, ff = pull()
        import pickle
        pickle.dump((crsp, dl, fund, link, ff), open(cache,"wb"))
    panel = build_us_panel(crsp, dl)
    f = prep_be(fund)
    assign = annual_sorts_us(panel, f, link)
    mine = compute(panel, assign)

    ff = ff.copy()
    ff.index = pd.PeriodIndex(ff["date"], freq="M")
    m = mine.join(ff[["mktrf","smb","hml","rmw","cma"]], how="inner", rsuffix="_ff").dropna()
    print(f"\n=== 재현 결과 vs French 공식 ({len(m)}개월, {m.index.min()}~{m.index.max()}) ===")
    lines = []
    # 자체 mkt은 총시장수익률 → French mktrf와 비교 시 rf 차감 필요 없음? mktrf=mkt-rf.
    # 상관은 rf가 저변동이라 mkt vs mktrf로도 유효하나 정확히: 비교는 상관계수 중심.
    for a, b in [("mkt","mktrf"),("smb","smb_ff"),("hml","hml_ff"),("rmw","rmw_ff"),("cma","cma_ff")]:
        r = m[a].corr(m[b])
        lines.append(f"{a.upper():6} vs French: corr = {r:.4f} | mean 자체 {m[a].mean()*100:+.3f}% vs FF {m[b].mean()*100:+.3f}%")
    print("\n".join(lines))
    with open(f"{OUT}/us_replication_results.md","w") as fh:
        fh.write("# 미국 재현 증명 결과\n\n표본: %s ~ %s (%d개월)\n\n```\n%s\n```\n"
                 % (m.index.min(), m.index.max(), len(m), "\n".join(lines)))

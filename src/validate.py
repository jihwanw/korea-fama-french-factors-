#!/usr/bin/env python3
"""검증: (1) Ken French APxJ 상관 (2) KOSPI 지수 대조 (3) 이벤트 정합성 (4) t-통계"""
import os, io, json, zipfile, urllib.request, configparser, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
OUT = os.path.dirname(os.path.abspath(__file__))
fac = pd.read_csv(f"{OUT}/factors_monthly_kr.csv", index_col=0, parse_dates=False)
fac.index = pd.PeriodIndex(fac.index, freq="M")

report = ["# 한국 FF 팩터 검증 결과 (Phase 1)\n"]

# ---------- 1. 기술통계 + t-stat ----------
report.append("## 1. 기술통계 (2001-07 ~ %s, %d개월)\n" % (fac.index.max(), len(fac)))
report.append("| 팩터 | 월평균(%) | 표준편차(%) | t-통계량 | 연율화 샤프 |")
report.append("|---|---|---|---|---|")
for c in ["MKT_RF", "SMB", "HML", "WML"]:
    s = fac[c].dropna()
    t = s.mean() / (s.std() / np.sqrt(len(s)))
    sharpe = s.mean() / s.std() * np.sqrt(12)
    report.append(f"| {c} | {s.mean():.3f} | {s.std():.3f} | {t:.2f} | {sharpe:.2f} |")
report.append("")

# ---------- 2. Ken French Asia Pacific ex Japan 대조 ----------
print("Ken French APxJ 3팩터 다운로드...")
url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Asia_Pacific_ex_Japan_3_Factors_CSV.zip"
try:
    raw = urllib.request.urlopen(url, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    csv_name = z.namelist()[0]
    lines = z.read(csv_name).decode("utf-8", errors="ignore").split("\n")
    # 월간 섹션 파싱 (YYYYMM 시작 행)
    rows = []
    for ln in lines:
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) >= 4 and len(parts[0]) == 6 and parts[0].isdigit():
            rows.append(parts[:5])
    ff = pd.DataFrame(rows, columns=["ym", "APxJ_MKT_RF", "APxJ_SMB", "APxJ_HML", "APxJ_RF"])
    ff = ff.astype({"APxJ_MKT_RF": float, "APxJ_SMB": float, "APxJ_HML": float})
    ff.index = pd.PeriodIndex(pd.to_datetime(ff["ym"], format="%Y%m"), freq="M")
    merged = fac.join(ff, how="inner")
    report.append("## 2. Ken French Asia Pacific ex Japan 대조 (겹치는 %d개월)\n" % len(merged))
    report.append("| 팩터 쌍 | 상관계수 |")
    report.append("|---|---|")
    for kr, us in [("MKT_RF", "APxJ_MKT_RF"), ("SMB", "APxJ_SMB"), ("HML", "APxJ_HML")]:
        r = merged[kr].corr(merged[us])
        report.append(f"| KR {kr} vs APxJ | {r:.3f} |")
    report.append("\n(한국은 APxJ의 일부이므로 완전 일치가 아닌 유의한 양의 상관이 기준. MKT이 가장 높아야 정상)\n")
except Exception as e:
    report.append(f"## 2. APxJ 대조 실패: {e}\n")

# ---------- 3. KOSPI 지수 대조 (ECOS 802Y001) ----------
print("ECOS KOSPI 지수 대조...")
cfg = configparser.ConfigParser(); cfg.read("/Users/jihwanw/PhD/code/api_info/api_keys.ini")
key = cfg.get("ecos", "api_key", fallback=None) or cfg.get("ecos", "key")
try:
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/1000/802Y001/M/200101/202612/0001000"
    data = json.loads(urllib.request.urlopen(url, timeout=30).read())
    rows = data["StatisticSearch"]["row"]
    kospi = pd.DataFrame([(r["TIME"], float(r["DATA_VALUE"])) for r in rows], columns=["ym", "kospi"])
    kospi.index = pd.PeriodIndex(pd.to_datetime(kospi["ym"], format="%Y%m"), freq="M")
    kospi["kospi_ret"] = kospi["kospi"].pct_change() * 100
    merged2 = fac.join(kospi[["kospi_ret"]], how="inner").dropna(subset=["MKT", "kospi_ret"])
    r = merged2["MKT"].corr(merged2["kospi_ret"])
    beta = np.polyfit(merged2["kospi_ret"], merged2["MKT"], 1)[0]
    report.append("## 3. 시장수익률 검증 (vs KOSPI 지수, %d개월)\n" % len(merged2))
    report.append(f"- 상관계수: **{r:.3f}** (기대: 0.95+)")
    report.append(f"- 회귀 기울기: {beta:.3f}")
    report.append("- 참고: 자체 MKT은 KOSDAQ 포함 + 배당 포함(총수익률), KOSPI 지수는 가격지수이므로 1보다 다소 낮은 상관이 정상\n")
except Exception as e:
    report.append(f"## 3. KOSPI 대조 실패: {e}\n")

# ---------- 4. 이벤트 정합성 ----------
report.append("## 4. 이벤트 정합성\n")
report.append("| 시점 | MKT_RF(%) | 기대 방향 |")
report.append("|---|---|---|")
for ym, label in [("2008-10", "글로벌 금융위기"), ("2020-03", "COVID 급락"), ("2020-04", "COVID 반등")]:
    p = pd.Period(ym, freq="M")
    if p in fac.index:
        v = fac.loc[p, "MKT_RF"]
        report.append(f"| {ym} ({label}) | {v:.2f} | {'급락' if '급락' in label or '위기' in label else '반등'} |")
report.append("")

with open(f"{OUT}/summary_stats.md", "w") as f:
    f.write("\n".join(report))
print("\n".join(report))

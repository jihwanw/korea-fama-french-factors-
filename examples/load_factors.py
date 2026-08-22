#!/usr/bin/env python3
"""예제 1: 팩터 로드와 기초 분석 — 처음 오신 분은 여기부터"""
import pandas as pd

URL = "https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors-/main/data/factors_monthly_kr_ff5.csv"
f = pd.read_csv(URL, index_col=0)          # 단위: % (월간)

# 1) 기초 통계 — 각 팩터의 월평균과 변동성
print(f[["MKT_RF","SMB","HML","RMW","CMA","WML"]].describe().loc[["mean","std"]].round(3))

# 2) 누적 수익률 — "2001년에 1을 넣었다면?"
cum = (1 + f[["MKT_RF","HML","WML"]].dropna()/100).cumprod()
print("\n누적 배수 (2001-07=1):")
print(cum.iloc[-1].round(2))

# 3) 내 포트폴리오의 알파 구하기 (개념 예시)
# 초과수익률 시계열 my_ret가 있다면:
#   import statsmodels.api as sm
#   X = sm.add_constant(f[["MKT_RF","SMB","HML","RMW","CMA"]])
#   model = sm.OLS(my_ret, X, missing="drop").fit()
#   print(model.params["const"])   # <- 월간 알파(%)

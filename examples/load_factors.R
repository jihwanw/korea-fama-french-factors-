# 예제: R에서 팩터 로드와 CAPM/FF5 회귀
url <- "https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors-/main/data/factors_monthly_kr_ff5.csv"
f <- read.csv(url)                     # 단위: % (월간)
head(f); summary(f[, c("MKT_RF","SMB","HML","RMW","CMA","WML")])

# 누적 수익률 그림
cum <- cumprod(1 + na.omit(f$MKT_RF)/100)
plot(cum, type = "l", main = "Korea Market Excess Return (cumulative)",
     xlab = "Months since 2001-07", ylab = "Growth of 1")

# 포트폴리오 초과수익률(my_ret)이 있다면 FF5 회귀:
# fit <- lm(my_ret ~ MKT_RF + SMB + HML + RMW + CMA, data = merged_df)
# summary(fit)   # (Intercept) = 월간 알파(%)

# Korea Fama-French Three Factors

한국 주식시장의 Fama-French 3 Factor 월별 데이터 (2020-10 ~ 현재)

[![Data Source](https://img.shields.io/badge/Data-WRDS%20Compustat%20Global-blue)](https://wrds-www.wharton.upenn.edu/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)

---

## 📊 데이터

### 파일 위치
- **`data/korea_factors_monthly.csv`** - 월별 3 Factor 데이터

### 데이터 구조
```csv
date,MKT,SMB,HML,RF
2020-10-31,-1.95,0.25,1.43,0.08
2020-11-30,15.22,0.59,-0.75,0.08
...
```

### 컬럼 설명
- **date**: 월말 날짜 (YYYY-MM-DD)
- **MKT**: Market Premium (%) = 시장수익률 - 무위험수익률
- **SMB**: Small Minus Big (%) = 소형주 - 대형주 수익률
- **HML**: High Minus Low (%) = 가치주 - 성장주 수익률
- **RF**: Risk-Free Rate (%) = 무위험수익률 (월 0.083% = 연 1%)

---

## 🔬 방법론

### Fama-French 3 Factor Model

**Stage 1: 포트폴리오 구성 (2x3 Sort)**

1. **Size 분류** (시가총액 기준)
   - Small (S): 중위수 이하
   - Big (B): 중위수 초과

2. **Value 분류** (Book-to-Market 기준)
   - Low (L): 상위 30% (가치주)
   - Medium (M): 중간 40%
   - High (H): 하위 30% (성장주)

3. **6개 포트폴리오**
   - S/L, S/M, S/H (소형주 3개)
   - B/L, B/M, B/H (대형주 3개)

**Stage 2: Factor 계산**

```
SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
HML = (S/L + B/L)/2 - (S/H + B/H)/2
MKT = 시장 가치가중 수익률 - RF
```

---

## 📥 데이터 출처

### 1. 주가 및 시가총액
- **출처**: WRDS Compustat Global Security Daily (`comp.g_secd`)
- **테이블**: `comp.g_secd`
- **필드**:
  - `prccd`: 종가 (Closing Price)
  - `ajexdi`: 조정계수 (Adjustment Factor)
  - `cshoc`: 발행주식수 (Shares Outstanding)
  - `market_cap = prccd / ajexdi * cshoc`

### 2. 장부가치 (Book Equity)
- **출처**: WRDS Compustat Global Fundamentals Annual (`comp.g_funda`)
- **테이블**: `comp.g_funda`
- **필드**:
  - `ceq`: 보통주 자본 (Common Equity)
  - 가장 최근 연간 데이터 사용

### 3. 무위험수익률 (Risk-Free Rate)
- **가정**: 연 1% (월 0.083%)
- **근거**: 한국 국고채 1년물 평균 수익률 근사치

### 4. 데이터 필터링
- **국가**: `fic = 'KOR'` (한국)
- **제외**: 가격 또는 발행주식수가 NULL인 종목
- **제외**: 장부가치가 없는 종목

---

## 🔄 데이터 업데이트

### 자동 업데이트
```bash
python korea_factor_updater.py
```

### 수동 업데이트 (특정 기간)
```bash
python korea_factor_updater.py --start-date 2020-10-01 --end-date 2025-12-31
```

---

## 🛠️ 사용 방법

### 1. 설치
```bash
pip install pandas numpy wrds
```

### 2. WRDS 설정
```json
{
  "username": "your_wrds_username",
  "password": "your_wrds_password"
}
```
파일명: `wrds_config.json` (gitignored)

### 3. 데이터 로드
```python
import pandas as pd

# 데이터 로드
factors = pd.read_csv('data/korea_factors_monthly.csv', parse_dates=['date'])

# 최근 데이터 확인
print(factors.tail())
```

---

## 📚 참고문헌

1. **Fama, E. F., & French, K. R. (1993)**  
   "Common risk factors in the returns on stocks and bonds"  
   *Journal of Financial Economics*, 33(1), 3-56.

2. **WRDS Compustat Global**  
   https://wrds-www.wharton.upenn.edu/

---

## 📄 라이선스

Academic Research Use Only

---

## 📞 문의

- GitHub: [@jihwanw](https://github.com/jihwanw)
- Repository: [korea-fama-french-factors](https://github.com/jihwanw/korea-fama-french-factors-)

---

**Last Updated**: 2025-10-22  
**Data Coverage**: 2020-10-31 to 2025-10-31 (61 months)

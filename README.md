# Korea Fama-French Three Factors

한국 주식시장의 Fama-French 3 Factor 월별 데이터 (2020-10 ~ 2025-10)

[![Data](https://img.shields.io/badge/Data-WRDS%20Compustat-blue)](https://wrds-www.wharton.upenn.edu/)
[![RF](https://img.shields.io/badge/RF-BOK%20ECOS-green)](https://ecos.bok.or.kr/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)
[![R](https://img.shields.io/badge/R-4.0+-red)](https://www.r-project.org/)

**한국어** | [English](README_EN.md)

---

## 📊 데이터

### 파일 구조
```
korea-fama-french-factors/
├── README.md                          # 한국어 문서
├── README_EN.md                       # 영어 문서
├── data/
│   └── korea_factors_monthly.csv      # 월별 3 Factor 데이터 (MKT, SMB, HML, RF)
├── docs/
│   ├── DATA_COLLECTION_WRDS.md        # WRDS 데이터 수집 가이드
│   └── DATA_COLLECTION_ECOS.md        # ECOS API 사용 가이드
├── korea_factor_calculator.py         # Factor 계산 로직
├── korea_factor_updater.py            # Factor 자동 업데이트
├── korea_rf_fetcher.py                # 무위험 수익률 수집
├── korea_ticker_utils.py              # WRDS 데이터 조회 유틸리티
└── fama_macbeth_test.py               # Fama-MacBeth 회귀 테스트
```

### Python 스크립트 설명

| 파일 | 설명 | 용도 |
|------|------|------|
| **korea_factor_calculator.py** | Fama-French 3 Factor 계산 | 포트폴리오 구성 및 Factor 계산 로직 |
| **korea_factor_updater.py** | Factor 데이터 자동 업데이트 | 누락된 월 자동 감지 및 계산 |
| **korea_rf_fetcher.py** | 무위험 수익률 수집 | 한국은행 ECOS API 연동 |
| **korea_ticker_utils.py** | WRDS 데이터 조회 | 주가, 시총, 장부가치 조회 함수 |
| **fama_macbeth_test.py** | Fama-MacBeth 회귀 테스트 | Factor 유의성 검정 및 통계 분석 |

### 데이터 형식
```csv
date,MKT,SMB,HML,RF
2020-10-31,-1.95,0.25,1.43,0.057
2020-11-30,15.22,0.59,-0.75,0.058
...
```

### 변수 설명
| 변수 | 설명 | 단위 |
|------|------|------|
| **date** | 월말 날짜 | YYYY-MM-DD |
| **MKT** | Market Premium = 시장수익률 - RF | % |
| **SMB** | Small Minus Big = 소형주 - 대형주 | % |
| **HML** | High Minus Low = 가치주 - 성장주 | % |
| **RF** | Risk-Free Rate = 국고채 1년 / 12 | % |

---

## 🔬 방법론

### Fama-French 3 Factor Model (1993)

#### 1단계: 포트폴리오 구성 (2x3 Sort)

**Size 분류** (시가총액 기준)
- Small (S): 중위수 이하
- Big (B): 중위수 초과

**Value 분류** (Book-to-Market 기준)
- Low (L): 상위 30% (가치주)
- Medium (M): 중간 40%
- High (H): 하위 30% (성장주)

**6개 포트폴리오**: S/L, S/M, S/H, B/L, B/M, B/H

#### 2단계: Factor 계산

```
SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
HML = (S/L + B/L)/2 - (S/H + B/H)/2
MKT = 시장 가치가중 수익률 - RF
```

---

## 📥 데이터 출처 및 수집 방법

### 1. 주가 및 시가총액

**출처**: WRDS Compustat Global Security Daily

**접근 방법**:
1. WRDS 계정 필요: https://wrds-www.wharton.upenn.edu/
2. 기관 구독 필요 (대학/연구기관)

**데이터베이스**: `comp.g_secd`

**SQL 쿼리 예시**:
```sql
SELECT gvkey, iid, datadate, conm, prccd, ajexdi, cshoc,
       (prccd / ajexdi * cshoc) as market_cap
FROM comp.g_secd
WHERE fic = 'KOR'
  AND datadate = '2020-10-31'
  AND prccd IS NOT NULL
  AND cshoc IS NOT NULL
ORDER BY market_cap DESC
```

**필드 설명**:
- `prccd`: 종가 (Closing Price)
- `ajexdi`: 조정계수 (Adjustment Factor for splits/dividends)
- `cshoc`: 발행주식수 (Shares Outstanding)
- `market_cap`: 시가총액 = prccd / ajexdi * cshoc

**상세 가이드**: [docs/DATA_COLLECTION_WRDS.md](docs/DATA_COLLECTION_WRDS.md)

---

### 2. 장부가치 (Book Equity)

**출처**: WRDS Compustat Global Fundamentals Annual

**데이터베이스**: `comp.g_funda`

**SQL 쿼리 예시**:
```sql
SELECT gvkey, datadate, ceq, at
FROM comp.g_funda
WHERE fic = 'KOR'
  AND datadate <= '2020-10-31'
  AND datadate >= '2018-10-31'
  AND ceq IS NOT NULL
  AND ceq > 0
ORDER BY datadate DESC
```

**필드 설명**:
- `ceq`: 보통주 자본 (Common Equity)
- `at`: 총자산 (Total Assets)

**처리 방법**: 각 종목의 가장 최근 연간 데이터 사용

---

### 3. 무위험 수익률 (Risk-Free Rate)

**출처**: 한국은행 경제통계시스템 (ECOS)

**API 접근 방법**:

1. **API 키 발급**
   - URL: https://ecos.bok.or.kr/
   - 회원가입 → 로그인 → "인증키 신청/관리"
   - 용도: "학술연구" 선택
   - 즉시 발급

2. **통계표 정보**
   - 통계표코드: `817Y002`
   - 통계항목코드: `010190000`
   - 통계명: 국고채(1년) 수익률
   - 주기: 일별(D)
   - 단위: 연율(%)

3. **API 호출 예시**
```bash
curl "https://ecos.bok.or.kr/api/StatisticSearch/YOUR_API_KEY/json/kr/1/10000/817Y002/D/20201001/20251031/010190000"
```

4. **데이터 처리**
   - 일별 데이터 → 월별 평균 계산
   - 연율(%) → 월율(%) 변환: `annual_rate / 12`

**Python 스크립트**: `korea_rf_fetcher.py`

**실행 방법**:
```bash
python korea_rf_fetcher.py --config config.json
```

**상세 가이드**: [docs/DATA_COLLECTION_ECOS.md](docs/DATA_COLLECTION_ECOS.md)

---

## 🔄 데이터 업데이트

### 무위험 수익률 업데이트
```bash
python korea_rf_fetcher.py --config config.json --start-date 20201001 --end-date 20251231
```

### Factor 재계산
```bash
python korea_factor_updater.py --filepath data/korea_factors_monthly.csv
```

### Factor 유의성 테스트
```bash
python fama_macbeth_test.py
```

---

## 💻 사용 방법

### Python

```bash
# 설치
pip install pandas numpy wrds requests
```

```python
import pandas as pd

# 데이터 로드
factors = pd.read_csv('data/korea_factors_monthly.csv', parse_dates=['date'])

# 요약 통계
print(factors.describe())
print(factors.tail())

# 누적 수익률 계산
factors['MKT_cum'] = (1 + factors['MKT']/100).cumprod() - 1
```

### R

```r
# 데이터 로드
factors <- read.csv('data/korea_factors_monthly.csv')
factors$date <- as.Date(factors$date)

# 요약 통계
summary(factors)
tail(factors)

# 누적 수익률 계산
factors$MKT_cum <- cumprod(1 + factors$MKT/100) - 1

# 시각화
library(ggplot2)
ggplot(factors, aes(x=date, y=MKT)) +
  geom_line() +
  labs(title="한국 시장 프리미엄", y="수익률 (%)")
```

---

## 📚 참고문헌

### 핵심 논문

1. **Fama, E. F., & MacBeth, J. D. (1973)**  
   "Risk, Return, and Equilibrium: Empirical Tests"  
   *Journal of Political Economy*, 81(3), 607-636.  
   DOI: [10.1086/260061](https://doi.org/10.1086/260061)

2. **Fama, E. F., & French, K. R. (1993)**  
   "Common risk factors in the returns on stocks and bonds"  
   *Journal of Financial Economics*, 33(1), 3-56.  
   DOI: [10.1016/0304-405X(93)90023-5](https://doi.org/10.1016/0304-405X(93)90023-5)

3. **Fama, E. F., & French, K. R. (2015)**  
   "A five-factor asset pricing model"  
   *Journal of Financial Economics*, 116(1), 1-22.  
   DOI: [10.1016/j.jfineco.2014.10.010](https://doi.org/10.1016/j.jfineco.2014.10.010)

### 데이터 출처

4. **WRDS Compustat Global**  
   Wharton Research Data Services  
   https://wrds-www.wharton.upenn.edu/

5. **한국은행 경제통계시스템 (ECOS)**  
   Bank of Korea Economic Statistics System  
   https://ecos.bok.or.kr/

### 방법론 참고

6. **Newey, W. K., & West, K. D. (1987)**  
   "A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix"  
   *Econometrica*, 55(3), 703-708.

7. **Cochrane, J. H. (2005)**  
   *Asset Pricing* (Revised Edition)  
   Princeton University Press.

### 추가 자료

- **Kenneth French Data Library**: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- **AQR Capital Management Datasets**: https://www.aqr.com/Insights/Datasets

---

## 📄 라이선스 및 면책사항

### 라이선스

**MIT License**

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### 학술 연구 목적

본 프로젝트는 **학술 연구 및 교육 목적으로만** 사용됩니다.

### 중요 면책사항

⚠️ **투자 조언 아님**
- 본 연구는 학술 목적으로만 제공되며 투자 조언이 아닙니다
- 연구 결과를 투자 결정의 유일한 근거로 사용해서는 안 됩니다
- 투자 결정 전 반드시 전문 금융 자문가와 상담하시기 바랍니다

⚠️ **과거 성과**
- 과거 성과가 미래 수익을 보장하지 않습니다
- 역사적 수익률은 미래 성과를 나타내지 않습니다
- 시장 상황은 변화하며 역사적 패턴이 지속되지 않을 수 있습니다

⚠️ **데이터 한계**
- 데이터에 오류, 누락 또는 부정확성이 포함될 수 있습니다
- 결과는 데이터 품질 및 방법론 선택에 민감합니다
- 생존편향 완화 노력에도 불구하고 역사적 분석에 영향을 미칠 수 있습니다

⚠️ **모델 리스크**
- 자산 가격 결정 모델은 현실의 단순화입니다
- 팩터 모델이 모든 위험 요인을 포착하지 못할 수 있습니다
- 모델 파라미터는 불확실성을 가지고 추정됩니다

⚠️ **보증 없음**
- 본 소프트웨어는 "있는 그대로" 제공되며 어떠한 보증도 없습니다
- 저자는 본 소프트웨어 사용으로 인한 손실이나 손해에 대해 책임지지 않습니다
- 사용자는 본 연구 사용과 관련된 모든 위험을 부담합니다

⚠️ **규제 준수**
- 사용자는 해당 증권법 준수에 대한 책임이 있습니다
- 본 연구는 증권 제공 또는 권유를 구성하지 않습니다
- 귀하의 관할권 내 규제 요구사항에 대해 법률 자문을 구하시기 바랍니다

### 데이터 출처 표시

- **WRDS Compustat Global**: © Wharton Research Data Services
- **한국은행 ECOS**: © Bank of Korea Economic Statistics System
- **Fama-French Methodology**: © Eugene F. Fama & Kenneth R. French

### 책임있는 사용

본 소프트웨어를 사용함으로써 귀하는 다음에 동의합니다:
1. 학술, 교육 또는 연구 목적으로만 사용
2. 투자 결정의 유일한 근거로 사용하지 않음
3. 출판물이나 발표에서 본 연구를 적절히 인용
4. 모든 해당 데이터 라이선스 계약 준수
5. 위에 설명된 한계와 위험을 인정

---

## 📞 문의

- GitHub: [@jihwanw](https://github.com/jihwanw)
- Repository: [korea-fama-french-factors](https://github.com/jihwanw/korea-fama-french-factors-)

---

**Last Updated**: 2025-10-22  
**Data Period**: 2020-10-31 to 2025-10-31 (61 months)  
**RF Source**: Bank of Korea ECOS API (Stat: 817Y002)

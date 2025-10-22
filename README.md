# Korea Fama-French Three Factors

한국 주식시장의 Fama-French 3 Factor 월별 데이터 (2020-10 ~ 2025-10)

[![Data](https://img.shields.io/badge/Data-WRDS%20Compustat-blue)](https://wrds-www.wharton.upenn.edu/)
[![RF](https://img.shields.io/badge/RF-BOK%20ECOS-green)](https://ecos.bok.or.kr/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)

---

## 📊 데이터

### 파일 구조
```
data/
├── korea_factors_monthly.csv    # 월별 3 Factor 데이터 (61개월)
└── korea_rf_monthly.csv          # 월별 무위험 수익률 원본 데이터
```

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

---

## 💻 사용 방법

### 설치
```bash
pip install pandas numpy wrds requests
```

### 데이터 로드
```python
import pandas as pd

# Factor 데이터
factors = pd.read_csv('data/korea_factors_monthly.csv', parse_dates=['date'])
print(factors.tail())

# 무위험 수익률만
rf = pd.read_csv('data/korea_rf_monthly.csv', parse_dates=['date'])
print(rf.describe())
```

---

## 📚 참고문헌

1. **Fama, E. F., & French, K. R. (1993)**  
   "Common risk factors in the returns on stocks and bonds"  
   *Journal of Financial Economics*, 33(1), 3-56.  
   DOI: 10.1016/0304-405X(93)90023-5

2. **WRDS Compustat Global**  
   Wharton Research Data Services  
   https://wrds-www.wharton.upenn.edu/

3. **한국은행 경제통계시스템 (ECOS)**  
   Bank of Korea Economic Statistics System  
   https://ecos.bok.or.kr/

---

## 📄 라이선스

Academic Research Use Only

---

## 📞 문의

- GitHub: [@jihwanw](https://github.com/jihwanw)
- Repository: [korea-fama-french-factors](https://github.com/jihwanw/korea-fama-french-factors-)

---

**Last Updated**: 2025-10-22  
**Data Period**: 2020-10-31 to 2025-10-31 (61 months)  
**RF Source**: Bank of Korea ECOS API (Stat: 817Y002)

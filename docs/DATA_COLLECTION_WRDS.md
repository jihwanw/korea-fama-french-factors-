# WRDS 데이터 수집 가이드

## 개요

WRDS (Wharton Research Data Services)에서 한국 주식 데이터를 수집하는 방법을 설명합니다.

---

## 1. WRDS 접근 권한

### 계정 생성
1. 소속 기관이 WRDS 구독 중인지 확인
2. 기관 이메일로 계정 생성: https://wrds-www.wharton.upenn.edu/register/
3. 승인 대기 (보통 1-2일)

### Python 라이브러리 설치
```bash
pip install wrds
```

### 인증 설정
```python
import wrds
conn = wrds.Connection()  # 첫 실행 시 username/password 입력
```

---

## 2. 데이터베이스 구조

### Compustat Global
- **Security Daily** (`comp.g_secd`): 일별 주가 데이터
- **Fundamentals Annual** (`comp.g_funda`): 연간 재무제표

### 한국 데이터 필터
```sql
WHERE fic = 'KOR'  -- Korea
```

---

## 3. 주가 및 시가총액 수집

### 특정 날짜의 모든 한국 주식
```python
import wrds
import pandas as pd

conn = wrds.Connection()

query = """
SELECT gvkey, iid, datadate, conm,
       prccd, ajexdi, cshoc,
       (prccd / ajexdi * cshoc) as market_cap
FROM comp.g_secd
WHERE fic = 'KOR'
  AND datadate = '2020-10-31'
  AND prccd IS NOT NULL
  AND cshoc IS NOT NULL
  AND cshoc > 0
ORDER BY market_cap DESC
"""

df = conn.raw_sql(query)
print(f"Retrieved {len(df)} stocks")
```

### 기간별 주가 데이터
```python
query = """
SELECT gvkey, iid, datadate, prccd, ajexdi, cshoc
FROM comp.g_secd
WHERE gvkey IN ('104604', '204049')  -- 특정 종목
  AND datadate BETWEEN '2020-10-01' AND '2020-10-31'
  AND prccd IS NOT NULL
ORDER BY gvkey, datadate
"""

prices = conn.raw_sql(query)
```

---

## 4. 장부가치 수집

### 최근 연간 재무제표
```python
query = """
SELECT gvkey, datadate, ceq, at
FROM comp.g_funda
WHERE fic = 'KOR'
  AND datadate <= '2020-10-31'
  AND datadate >= '2018-10-31'
  AND ceq IS NOT NULL
  AND ceq > 0
ORDER BY gvkey, datadate DESC
"""

fundamentals = conn.raw_sql(query)

# 각 종목의 가장 최근 데이터만 선택
latest = fundamentals.groupby('gvkey').first().reset_index()
```

---

## 5. 데이터 필드 설명

### Security Daily (g_secd)
| 필드 | 설명 | 단위 |
|------|------|------|
| `gvkey` | Global Company Key | 고유 ID |
| `iid` | Issue ID | 증권 ID |
| `datadate` | 날짜 | YYYY-MM-DD |
| `conm` | 회사명 | 텍스트 |
| `prccd` | Closing Price | 현지 통화 |
| `ajexdi` | Adjustment Factor | 배수 |
| `cshoc` | Shares Outstanding | 주 |
| `curcdd` | Currency Code | KRW |

### Fundamentals Annual (g_funda)
| 필드 | 설명 | 단위 |
|------|------|------|
| `gvkey` | Global Company Key | 고유 ID |
| `datadate` | Fiscal Year End | YYYY-MM-DD |
| `ceq` | Common Equity | 백만 현지통화 |
| `at` | Total Assets | 백만 현지통화 |

---

## 6. 시가총액 계산

### 공식
```
Market Cap = (Price / Adjustment Factor) × Shares Outstanding
           = prccd / ajexdi × cshoc
```

### 조정계수 (ajexdi)
- 주식분할, 배당 등을 반영
- 시계열 비교 가능하도록 조정

---

## 7. Book-to-Market 계산

### 공식
```
Book-to-Market = Book Equity / Market Cap
               = ceq / (prccd / ajexdi × cshoc)
```

### 주의사항
1. Book Equity는 가장 최근 연간 데이터 사용
2. Market Cap은 포트폴리오 구성 시점 데이터 사용
3. Book Equity가 음수인 종목 제외

---

## 8. 코드 예시

### 전체 프로세스
```python
import wrds
import pandas as pd
from datetime import datetime

# WRDS 연결
conn = wrds.Connection()

# 1. 특정 날짜의 주가 및 시총
date = '2020-10-31'
price_query = f"""
SELECT gvkey, iid, conm, prccd, ajexdi, cshoc,
       (prccd / ajexdi * cshoc) as market_cap
FROM comp.g_secd
WHERE fic = 'KOR'
  AND datadate = '{date}'
  AND prccd IS NOT NULL
  AND cshoc IS NOT NULL
  AND cshoc > 0
"""
prices = conn.raw_sql(price_query)

# 2. 장부가치
year = int(date[:4])
fund_query = f"""
SELECT gvkey, datadate, ceq
FROM comp.g_funda
WHERE fic = 'KOR'
  AND datadate <= '{date}'
  AND datadate >= '{year-2}-01-01'
  AND ceq IS NOT NULL
  AND ceq > 0
"""
fundamentals = conn.raw_sql(fund_query)
fundamentals = fundamentals.sort_values('datadate', ascending=False)
fundamentals = fundamentals.groupby('gvkey').first().reset_index()

# 3. 병합
merged = prices.merge(fundamentals[['gvkey', 'ceq']], on='gvkey', how='left')
merged['book_to_market'] = merged['ceq'] / merged['market_cap']

# 4. 결과
print(f"Total stocks: {len(merged)}")
print(f"With B/M: {merged['book_to_market'].notna().sum()}")
print(merged[['conm', 'market_cap', 'book_to_market']].head(10))

conn.close()
```

---

## 9. 문제 해결

### 연결 오류
```python
# 인증 정보 재설정
import wrds
conn = wrds.Connection(wrds_username='your_username')
```

### 데이터 없음
- 날짜가 거래일인지 확인
- 주말/공휴일에는 데이터 없음
- `datadate <= 'YYYY-MM-DD'`로 이전 거래일 찾기

### 느린 쿼리
- `LIMIT` 사용하여 테스트
- 필요한 컬럼만 SELECT
- 인덱스 활용 (gvkey, datadate)

---

## 10. 참고 자료

- WRDS Documentation: https://wrds-www.wharton.upenn.edu/pages/support/
- Compustat Manual: https://wrds-www.wharton.upenn.edu/pages/get-data/compustat/
- WRDS Python Package: https://pypi.org/project/wrds/

---

**작성일**: 2025-10-22  
**업데이트**: 필요 시 WRDS 웹사이트 참조

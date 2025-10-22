# 한국 시장 Size Premium 분석 계획

**목적**: 미국 시장에서 발견된 Size Premium 역전 현상이 한국 시장에도 존재하는지 검증  
**분석 기간**: 2020년 10월 ~ 2025년 10월 (미국과 동일)  
**작성 일자**: 2025년 10월 21일

---

## 1. 데이터 소스

### 1.1 한국 주식 데이터

#### 옵션 A: WRDS - Global Compustat & DataStream (추천 ⭐)
- **장점**: 
  - 이미 WRDS 계정 보유
  - 과거 시가총액 데이터 정확
  - 학술 연구용으로 신뢰성 높음
- **데이터베이스**: 
  - `comp.g_secd` (Global Compustat Daily)
  - `tfn.wrds_dss2` (DataStream)
- **필요 정보**: 
  - 한국 주식 (gvkey, isin 코드)
  - 일별 주가, 시가총액
  - 2020-2025년 데이터

```python
# WRDS 쿼리 예시
query = """
SELECT date, gvkey, isin, prccd, cshoc, mkvaltq
FROM comp.g_secd
WHERE fic = 'KOR'  -- 한국
AND datadate BETWEEN '2020-10-01' AND '2025-10-31'
AND prccd IS NOT NULL
ORDER BY date, mkvaltq DESC
"""
```

#### 옵션 B: FinanceDataReader (무료, 간편)
- **장점**: 
  - 무료
  - Python 라이브러리로 쉽게 사용
  - 한국 시장 특화
- **단점**: 
  - 과거 시가총액 데이터 제한적
  - 학술 연구용 신뢰성 검증 필요
- **설치**: `pip install finance-datareader`

```python
import FinanceDataReader as fdr

# KOSPI 전체 종목 리스트
krx_stocks = fdr.StockListing('KRX')

# 개별 주식 데이터
samsung = fdr.DataReader('005930', '2020-10-01', '2025-10-31')
```

#### 옵션 C: pykrx (한국거래소 공식 API, 무료)
- **장점**: 
  - 한국거래소 공식 데이터
  - 무료
  - 시가총액 데이터 정확
- **단점**: 
  - API 속도 제한
  - 대량 데이터 수집 시간 소요
- **설치**: `pip install pykrx`

```python
from pykrx import stock

# 2020년 10월 특정일 시가총액 상위 100개
df = stock.get_market_cap_by_ticker("20201018", market="ALL")
top100 = df.nlargest(100, '시가총액')
```

### 1.2 Fama-French 팩터 데이터 (한국)

#### 옵션 A: AQR Capital Management (추천 ⭐⭐⭐)
- **URL**: https://www.aqr.com/Insights/Datasets
- **데이터셋**: "International Factors"
- **포함 국가**: 한국 포함 (Korea)
- **팩터**: 
  - Market (MKT)
  - Size (SMB)
  - Value (HML)
  - Momentum (UMD)
- **기간**: 1990년대 ~ 현재
- **형식**: Excel/CSV
- **장점**: 
  - 무료
  - 학술 연구용으로 널리 사용
  - Kenneth French 방법론과 유사

#### 옵션 B: 직접 계산
- Fama-French 방법론에 따라 직접 계산
- 필요 데이터:
  - 전체 주식의 시가총액
  - Book-to-Market ratio
  - 월별 수익률
- **장점**: 완전한 통제
- **단점**: 복잡하고 시간 소요

#### 옵션 C: WRDS - Global Fama-French Factors
- WRDS에서 제공하는 글로벌 팩터
- 한국 포함 여부 확인 필요

---

## 2. 실험 계획

### 2.1 Phase 1: 데이터 수집 및 검증

#### Step 1: 한국 주식 데이터 수집
```
목표: 2020년 10월 기준 시가총액 상위 100개 종목 선정

방법:
1. WRDS Compustat Global 또는 pykrx 사용
2. 2020년 10월 18일 기준 시가총액 조회
3. 상위 100개 종목 티커 추출
4. 2020-10-18 ~ 2025-10-17 일별 수익률 수집
```

#### Step 2: Fama-French 팩터 데이터 수집
```
목표: 한국 시장 MKT, SMB, HML 팩터 확보

방법:
1. AQR 웹사이트에서 International Factors 다운로드
2. Korea 시트 추출
3. 2020-10-18 ~ 2025-10-17 기간 필터링
4. 일별 데이터로 변환 (월별인 경우)
```

#### Step 3: 데이터 검증
```
체크리스트:
- [ ] 100개 종목 모두 데이터 확보
- [ ] 결측치 확인 및 처리
- [ ] 팩터 데이터 기간 일치
- [ ] 수익률 계산 정확성 검증
```

### 2.2 Phase 2: Fama-MacBeth 분석

#### Step 1: 1단계 시계열 회귀 (개별 주식)
```python
# 각 주식에 대해 시계열 회귀
R_i,t - R_f,t = α_i + β_i,MKT * MKT_t + β_i,SMB * SMB_t + β_i,HML * HML_t + ε_i,t

결과: 각 주식의 β_MKT, β_SMB, β_HML 추정
```

#### Step 2: 2단계 횡단면 회귀 (월별)
```python
# 매월 횡단면 회귀
R_i,t = γ_0,t + γ_MKT,t * β_i,MKT + γ_SMB,t * β_i,SMB + γ_HML,t * β_i,HML + ε_i,t

결과: 월별 팩터 프리미엄 γ_t
```

#### Step 3: 평균 프리미엄 및 통계적 검정
```python
# 시간 평균
γ_MKT = mean(γ_MKT,t)
γ_SMB = mean(γ_SMB,t)
γ_HML = mean(γ_HML,t)

# t-검정
t_SMB = γ_SMB / SE(γ_SMB,t)
p_value = ...
```

### 2.3 Phase 3: 결과 비교

#### 비교 항목
| 지표 | 미국 시장 | 한국 시장 | 해석 |
|------|---------|---------|------|
| Size Premium | -28.37% | ? | 역전 여부 |
| p-value | 0.005 | ? | 통계적 유의성 |
| Market Premium | 28.13% | ? | 시장 위험 프리미엄 |
| Value Premium | 9.06% | ? | 가치 효과 |

#### 가설
- **H1**: 한국 시장에서도 Size Premium 역전 발생
- **H2**: 한국 시장의 역전이 미국보다 강함 (신흥시장 특성)
- **H3**: 한국 시장의 Value Premium도 약화됨

---

## 3. 구현 계획

### 3.1 파일 구조
```
finance-research/
├── run_korea_analysis.py          # 한국 시장 분석 메인 스크립트
├── korea_ticker_utils.py          # 한국 티커 유틸리티
├── korea_factor_loader.py         # AQR 팩터 로더
├── data/
│   ├── korea_factors_aqr.csv      # AQR 한국 팩터
│   └── kospi_top100_2020-10-18.csv # 한국 상위 100개
└── results/
    ├── korea_stage1_betas.csv
    ├── korea_stage2_cross_sectional.csv
    └── korea_fama_macbeth_output.txt
```

### 3.2 코드 재사용
```python
# 미국 분석 코드 재사용
# run_dynamic_analysis.py 기반으로 수정

주요 변경사항:
1. 티커 소스: WRDS CRSP → WRDS Compustat Global / pykrx
2. 팩터 소스: Kenneth French → AQR Korea
3. 무위험 이자율: US Treasury → 한국 국고채 (또는 AQR 제공)
```

### 3.3 예상 소요 시간
- **데이터 수집**: 2-3시간
- **코드 수정**: 1-2시간
- **분석 실행**: 30분
- **결과 검증**: 1시간
- **총 예상 시간**: 5-7시간

---

## 4. 데이터 소스 추천 (최종)

### 추천 조합 ⭐
1. **주식 데이터**: pykrx (무료, 정확, 한국 특화)
2. **팩터 데이터**: AQR International Factors (무료, 학술 표준)
3. **무위험 이자율**: AQR 제공 또는 한국은행 기준금리

### 이유
- 빠른 구현 가능
- 무료
- 학술 연구용으로 신뢰성 높음
- WRDS는 백업으로 활용

---

## 5. 다음 단계

### 즉시 실행 가능한 작업
1. **AQR 데이터 다운로드**
   - https://www.aqr.com/Insights/Datasets
   - "International Factors" 다운로드
   - Korea 시트 확인

2. **pykrx 설치 및 테스트**
   ```bash
   pip install pykrx
   ```
   
   ```python
   from pykrx import stock
   df = stock.get_market_cap_by_ticker("20201018", market="ALL")
   print(df.head(100))
   ```

3. **데이터 검증**
   - 2020년 10월 시가총액 상위 100개 확인
   - AQR 팩터 데이터 기간 확인 (2020-2025 포함 여부)

### 확인 후 진행
- 데이터 확보 확인되면 코드 작성 시작
- 미국 분석 코드 기반으로 한국 버전 개발

---

## 6. 예상 논문 기여도

### 단일 국가 분석 (미국만)
- 기여도: 중간
- 한계: 미국 특수 현상일 가능성

### 다국가 비교 (미국 + 한국) ⭐⭐⭐
- 기여도: 높음
- 강점:
  - 글로벌 현상 입증
  - 선진시장 vs 신흥시장 비교
  - 논문 임팩트 크게 향상
  - Top-tier 저널 가능성 증가

### 추가 확장 가능성
- 일본, 유럽 시장 추가 분석
- 지역별 차이 분석
- 시장 성숙도와 Size Premium 관계 연구

---

## 7. 리스크 및 대응

### 리스크 1: 한국 팩터 데이터 부족
- **대응**: 직접 계산 (시간 소요 증가)
- **백업**: WRDS Global Fama-French 확인

### 리스크 2: 한국 시장 결과가 미국과 다름
- **대응**: 차이의 원인 분석 (시장 구조, 규제 등)
- **논문 각도**: "Why Size Premium Reversal Differs Across Markets"

### 리스크 3: 데이터 품질 문제
- **대응**: 여러 소스 교차 검증
- **백업**: WRDS 데이터 활용

---

## 8. 체크리스트

### 데이터 확보 전
- [ ] AQR 웹사이트에서 Korea 팩터 데이터 다운로드
- [ ] pykrx 설치 및 2020년 시가총액 데이터 확인
- [ ] 데이터 기간 일치 확인 (2020-10 ~ 2025-10)
- [ ] 무위험 이자율 데이터 확보

### 코드 개발 전
- [ ] 데이터 품질 검증 완료
- [ ] 미국 코드 리뷰 및 재사용 가능 부분 식별
- [ ] 한국 시장 특수성 파악 (거래 정지, 상장폐지 등)

### 분석 실행 전
- [ ] 테스트 데이터로 파이프라인 검증
- [ ] 결과 해석 방법 준비
- [ ] 미국 결과와 비교 프레임워크 준비

---

**다음 단계**: AQR 데이터 다운로드 및 pykrx 테스트 후 진행 여부 결정

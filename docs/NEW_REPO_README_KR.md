# 한국 주식시장 Fama-French 3 팩터

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: Monthly](https://img.shields.io/badge/Data-Monthly-blue.svg)]()
[![Period: 2020-2025](https://img.shields.io/badge/Period-2020--2025-green.svg)]()

**한국 주식시장의 월별 Fama-French 3 팩터 데이터**

[한국어 README](README_KR.md) | [English README](README.md)

---

## 📊 이것은 무엇인가요?

이 저장소는 미국 시장의 [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)와 유사하게, 한국 주식시장의 월별 Fama-French 3 팩터를 제공합니다.

**제공 팩터:**
- **MKT**: 시장 프리미엄 (Market Premium)
- **SMB**: 규모 프리미엄 - Small Minus Big (Size Premium)
- **HML**: 가치 프리미엄 - High Minus Low (Value Premium)
- **RF**: 무위험 이자율 (Risk-Free Rate)

---

## 🚀 빠른 시작

### 데이터 다운로드

**직접 다운로드:**
```
https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors/main/data/korea_factors_monthly.csv
```

### Python 사용

```python
import pandas as pd

# 한국 Fama-French 팩터 로드
url = 'https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors/main/data/korea_factors_monthly.csv'
factors = pd.read_csv(url, parse_dates=['date'])

print(factors.head())
print(f"\n데이터 기간: {factors['date'].min()} ~ {factors['date'].max()}")
print(f"데이터 개월 수: {len(factors)}개월")

# 예시: 누적 수익률 계산
factors['MKT_cumulative'] = (1 + factors['MKT']/100).cumprod() - 1
print(f"\n누적 시장 수익률: {factors['MKT_cumulative'].iloc[-1]*100:.2f}%")
```

### R 사용

```r
library(tidyverse)

# 한국 Fama-French 팩터 로드
url <- "https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors/main/data/korea_factors_monthly.csv"
factors <- read_csv(url)

head(factors)

# 요약 통계
factors %>%
  select(MKT, SMB, HML) %>%
  summary()
```

---

## 📈 데이터 요약

### 기간
- **시작**: 2020년 10월
- **종료**: 2025년 9월
- **빈도**: 월별
- **관측치**: 45개월

### 요약 통계

| 팩터 | 평균 | 표준편차 | 최소값 | 최대값 |
|------|------|---------|--------|--------|
| MKT  | 1.68% | 5.90% | -12.93% | 15.22% |
| SMB  | 0.45% | 3.07% | -9.43% | 5.88% |
| HML  | -0.98% | 4.06% | -10.06% | 6.99% |
| RF   | 0.08% | 0.00% | 0.08% | 0.08% |

### 최신 데이터 (2025년)

| 월 | MKT | SMB | HML | RF |
|----|-----|-----|-----|-----|
| 2025-02 | 2.01% | 0.70% | -3.62% | 0.08% |
| 2025-05 | 6.55% | -2.58% | 2.66% | 0.08% |
| 2025-06 | 15.01% | -3.22% | -1.38% | 0.08% |
| 2025-08 | -1.12% | 0.64% | -1.82% | 0.08% |
| 2025-09 | 9.08% | -3.17% | 5.26% | 0.08% |

---

## 📖 방법론

### 포트폴리오 구성

Fama and French (1993)를 따라 규모와 장부가/시가 비율을 기준으로 6개의 가치가중 포트폴리오를 구성합니다:

**1. 규모 분류**
- **Small (S)**: 시가총액 중앙값 이하
- **Big (B)**: 시가총액 중앙값 이상

**2. 가치 분류 (장부가/시가 비율)**
- **Value (L)**: 상위 30%
- **Neutral (M)**: 중간 40%
- **Growth (H)**: 하위 30%

**3. 6개 포트폴리오**
- S/L (소형 가치주), S/M (소형 중립주), S/H (소형 성장주)
- B/L (대형 가치주), B/M (대형 중립주), B/H (대형 성장주)

### 팩터 계산식

```
SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
HML = (S/L + B/L)/2 - (S/H + B/H)/2
MKT = 시가총액 가중 시장 수익률 - RF
```

### 데이터 출처

- **주가 데이터**: WRDS Compustat Global (comp.g_secd)
- **재무제표 데이터**: WRDS Compustat Global Fundamentals (comp.g_funda)
- **대상 종목**: 한국 전체 주식 (fic='KOR')
- **리밸런싱**: 매년 6월
- **가중 방식**: 시가총액 가중

---

## 💻 코드

### 팩터 계산

```bash
# 필요한 패키지 설치
pip install -r requirements.txt

# 전체 기간 팩터 계산
python korea_factor_calculator.py

# 최신 월 데이터로 업데이트
python korea_factor_updater.py
```

자세한 구현:
- `korea_factor_calculator.py`: 팩터 계산 엔진
- `korea_ticker_utils.py`: 데이터 수집 유틸리티
- `korea_factor_updater.py`: 월별 업데이트 스크립트

---

## 🔄 업데이트 일정

매월 **5일**에 전월 데이터로 업데이트됩니다.

---

## 📚 인용

연구에 이 데이터를 사용하시는 경우 다음과 같이 인용해주세요:

```bibtex
@misc{korea_ff_factors_2025,
  author = {Woo, Jihwan, Ph.D.},
  title = {한국 주식시장 Fama-French 3 팩터: 월별 팩터 데이터},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/jihwanw/korea-fama-french-factors}
}
```

### 원 방법론

```bibtex
@article{fama1993common,
  title={Common risk factors in the returns on stocks and bonds},
  author={Fama, Eugene F and French, Kenneth R},
  journal={Journal of Financial Economics},
  volume={33},
  number={1},
  pages={3--56},
  year={1993},
  publisher={Elsevier}
}
```

---

## 🌟 왜 이 데이터를 사용하나요?

### 연구자를 위해
- ✅ **표준화**: Fama-French (1993) 방법론 준수
- ✅ **투명성**: 전체 코드 공개
- ✅ **재현 가능**: 계산 검증 가능
- ✅ **최신**: 월별 업데이트

### 다른 대안과 비교
- ❌ Kenneth French Library: 한국 전용 팩터 없음
- ❌ AQR: 지역 팩터만 제공 (Asia Pacific, 한국 단독 아님)
- ✅ **이 저장소**: 순수 한국 시장 팩터

---

## 📊 주요 발견

### Size Premium (SMB)
- **평균**: +0.45% (월별)
- **해석**: 한국 시장에서 소형주가 대형주보다 약간 높은 수익
- **최근 추세**: 2025년 들어 음수로 전환 (대형주 우세)

### Value Premium (HML)
- **평균**: -0.98% (월별)
- **해석**: 한국 시장에서 성장주가 가치주보다 높은 수익
- **특징**: 미국 시장과 유사한 패턴

### Market Premium (MKT)
- **평균**: +1.68% (월별), 약 20% (연간)
- **변동성**: 5.90% (월별 표준편차)

---

## 📞 연락처

- **저자**: 우지환 박사 (Dr. Jihwan Woo, Ph.D.)
- **GitHub**: [@jihwanw](https://github.com/jihwanw)
- **문의**: [Issues](https://github.com/jihwanw/korea-fama-french-factors/issues)

---

## 📄 라이선스

MIT 라이선스 - 학술 및 상업적 목적으로 자유롭게 사용 가능합니다.

---

## 🙏 감사의 말

- Kenneth French 교수님의 원 방법론과 영감
- WRDS의 Compustat Global 데이터 제공
- 이 데이터를 사용할 모든 연구자분들

---

## ⚠️ 면책 조항

이 데이터는 연구 목적으로만 제공됩니다. 저자는 데이터의 정확성이나 완전성에 대해 보증하지 않습니다. 사용자는 사용 전 데이터를 검증할 책임이 있습니다.

---

## 📊 관련 연구

이 데이터는 글로벌 시장의 Size Premium 연구의 일환으로 개발되었습니다. 

주요 연구 저장소: [finance-research](https://github.com/jihwanw/finance-research)

---

## 🔗 유용한 링크

- [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) - 미국 시장 팩터
- [AQR Data Sets](https://www.aqr.com/Insights/Datasets) - 글로벌 팩터
- [WRDS](https://wrds-www.wharton.upenn.edu/) - 금융 데이터베이스

---

**마지막 업데이트**: 2025년 10월

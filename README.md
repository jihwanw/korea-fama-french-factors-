# Korea Fama-French 3 Factors

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: Monthly](https://img.shields.io/badge/Data-Monthly-blue.svg)]()
[![Period: 2020-2025](https://img.shields.io/badge/Period-2020--2025-green.svg)]()

**Monthly Fama-French 3 Factors for the Korean Stock Market**

한국 주식시장의 월별 Fama-French 3 팩터 데이터를 제공합니다.

[한국어 README](README_KR.md) | [English README](README.md)

---

## 📊 What is This? (이것은 무엇인가요?)

This repository provides monthly Fama-French 3 factors for the Korean stock market, similar to [Kenneth French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) for the US market.

Kenneth French 교수의 미국 시장 데이터 라이브러리와 유사하게, 한국 주식시장의 월별 Fama-French 3 팩터를 제공합니다.

**Factors (팩터):**
- **MKT**: Market premium (시장 프리미엄)
- **SMB**: Size premium - Small Minus Big (규모 프리미엄)
- **HML**: Value premium - High Minus Low (가치 프리미엄)
- **RF**: Risk-free rate (무위험 이자율)

---

## 🚀 Quick Start

### Download Data (데이터 다운로드)

**Direct Download:**
```
https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors/main/data/korea_factors_monthly.csv
```

### Python

```python
import pandas as pd

# Load Korea Fama-French factors
url = 'https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors/main/data/korea_factors_monthly.csv'
factors = pd.read_csv(url, parse_dates=['date'])

print(factors.head())
print(f"\nData period: {factors['date'].min()} to {factors['date'].max()}")
print(f"Number of months: {len(factors)}")

# Example: Calculate cumulative returns
factors['MKT_cumulative'] = (1 + factors['MKT']/100).cumprod() - 1
print(f"\nCumulative market return: {factors['MKT_cumulative'].iloc[-1]*100:.2f}%")
```

### R

```r
library(tidyverse)

# Load Korea Fama-French factors
url <- "https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors/main/data/korea_factors_monthly.csv"
factors <- read_csv(url)

head(factors)

# Summary statistics
factors %>%
  select(MKT, SMB, HML) %>%
  summary()
```

---

## 📈 Data Summary (데이터 요약)

### Period (기간)
- **Start**: October 2020 (2020년 10월)
- **End**: September 2025 (2025년 9월)
- **Frequency**: Monthly (월별)
- **Observations**: 45 months (45개월)

### Summary Statistics (요약 통계)

| Factor | Mean (평균) | Std Dev (표준편차) | Min (최소) | Max (최대) |
|--------|------------|-------------------|-----------|-----------|
| MKT    | 1.68%      | 5.90%             | -12.93%   | 15.22%    |
| SMB    | 0.45%      | 3.07%             | -9.43%    | 5.88%     |
| HML    | -0.98%     | 4.06%             | -10.06%   | 6.99%     |
| RF     | 0.08%      | 0.00%             | 0.08%     | 0.08%     |

### Latest Data (최신 데이터 - 2025년)

| Month | MKT | SMB | HML | RF |
|-------|-----|-----|-----|-----|
| 2025-02 | 2.01% | 0.70% | -3.62% | 0.08% |
| 2025-05 | 6.55% | -2.58% | 2.66% | 0.08% |
| 2025-06 | 15.01% | -3.22% | -1.38% | 0.08% |
| 2025-08 | -1.12% | 0.64% | -1.82% | 0.08% |
| 2025-09 | 9.08% | -3.17% | 5.26% | 0.08% |

---

## 📖 Methodology (방법론)

### Portfolio Construction (포트폴리오 구성)

Following Fama and French (1993), we construct six value-weighted portfolios based on size and book-to-market ratio:

Fama and French (1993)를 따라 규모와 장부가/시가 비율 기준으로 6개의 가치가중 포트폴리오를 구성합니다:

**1. Size Breakpoint (규모 분류)**
- **Small (S)**: Below median market cap (시가총액 중앙값 이하)
- **Big (B)**: Above median market cap (시가총액 중앙값 이상)

**2. Book-to-Market Breakpoint (가치 분류)**
- **Value (L)**: Top 30% B/M ratio (장부가/시가 상위 30%)
- **Neutral (M)**: Middle 40% B/M ratio (장부가/시가 중간 40%)
- **Growth (H)**: Bottom 30% B/M ratio (장부가/시가 하위 30%)

**3. Six Portfolios (6개 포트폴리오)**
- S/L (Small Value), S/M (Small Neutral), S/H (Small Growth)
- B/L (Big Value), B/M (Big Neutral), B/H (Big Growth)

### Factor Calculation (팩터 계산식)

```
SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
HML = (S/L + B/L)/2 - (S/H + B/H)/2
MKT = Value-weighted market return - RF
```

### Data Source (데이터 출처)

- **Stock Prices**: WRDS Compustat Global (comp.g_secd)
- **Fundamentals**: WRDS Compustat Global Fundamentals (comp.g_funda)
- **Universe**: All Korean stocks (fic='KOR')
- **Rebalancing**: Annual in June (매년 6월 리밸런싱)
- **Weighting**: Value-weighted (시가총액 가중)

---

## 💻 Code (코드)

### Calculate Factors (팩터 계산)

```bash
# Install dependencies
pip install -r requirements.txt

# Calculate factors for entire period
python korea_factor_calculator.py

# Update with latest month
python korea_factor_updater.py
```

See detailed implementation in:
- `korea_factor_calculator.py`: Main calculation engine
- `korea_ticker_utils.py`: Data retrieval utilities
- `korea_factor_updater.py`: Monthly update script

자세한 구현은 다음 파일을 참조하세요:
- `korea_factor_calculator.py`: 팩터 계산 엔진
- `korea_ticker_utils.py`: 데이터 수집 유틸리티
- `korea_factor_updater.py`: 월별 업데이트 스크립트

---

## 🔄 Update Schedule (업데이트 일정)

Factors are updated **monthly** on the 5th of each month with the previous month's data.

매월 **5일**에 전월 데이터로 업데이트됩니다.

---

## 📚 Citation (인용)

If you use this data in your research, please cite:

연구에 이 데이터를 사용하시는 경우 다음과 같이 인용해주세요:

```bibtex
@misc{korea_ff_factors_2025,
  author = {Woo, Jihwan, Ph.D.},
  title = {Korea Fama-French 3 Factors: Monthly Factor Data for Korean Stock Market},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/jihwanw/korea-fama-french-factors}
}
```

### Original Methodology (원 방법론)

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

## 🌟 Why Use This Data? (왜 이 데이터를 사용하나요?)

### For Researchers (연구자를 위해)
- ✅ **Standardized**: Follows Fama-French (1993) methodology (표준화된 방법론)
- ✅ **Transparent**: Full code available (투명한 코드 공개)
- ✅ **Reproducible**: Can verify calculations (재현 가능)
- ✅ **Updated**: Monthly updates (월별 업데이트)

### Compared to Alternatives (다른 대안과 비교)
- ❌ Kenneth French Library: No Korea-specific factors (한국 전용 팩터 없음)
- ❌ AQR: Only regional factors (Asia Pacific, not Korea-only) (지역 팩터만 제공)
- ✅ **This Repository**: Pure Korean market factors (순수 한국 시장 팩터)

---

## 📞 Contact (연락처)

- **Author**: Dr. Jihwan Woo (Ph.D.)
- **GitHub**: [@jihwanw](https://github.com/jihwanw)
- **Issues**: [Report issues](https://github.com/jihwanw/korea-fama-french-factors/issues)

---

## 📄 License

MIT License - Free to use for academic and commercial purposes.

MIT 라이선스 - 학술 및 상업적 목적으로 자유롭게 사용 가능합니다.

---

## 🙏 Acknowledgments (감사의 말)

- Kenneth French for the original methodology and inspiration
- WRDS for providing Compustat Global data
- All researchers who will use this data

---

## ⚠️ Disclaimer (면책 조항)

This data is provided for research purposes only. The author makes no warranties about the accuracy or completeness of the data. Users are responsible for verifying the data before use.

이 데이터는 연구 목적으로만 제공됩니다. 저자는 데이터의 정확성이나 완전성에 대해 보증하지 않습니다. 사용자는 사용 전 데이터를 검증할 책임이 있습니다.

---

## 📊 Related Research (관련 연구)

This data was developed as part of research on the Size Premium in global markets. See the main research repository: [finance-research](https://github.com/jihwanw/finance-research)

이 데이터는 글로벌 시장의 Size Premium 연구의 일환으로 개발되었습니다. 주요 연구 저장소: [finance-research](https://github.com/jihwanw/finance-research)

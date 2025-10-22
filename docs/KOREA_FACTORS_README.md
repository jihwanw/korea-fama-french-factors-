# Korean Fama-French Three Factors
# 한국 주식시장 Fama-French 3 팩터

![Data Updated](https://img.shields.io/badge/Data%20Updated-2025--10-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

Monthly Fama-French Three Factors (MKT, SMB, HML) for the Korean Stock Market, calculated using WRDS Compustat Global data.

한국 주식시장의 Fama-French 3 팩터(시장, 규모, 가치)를 WRDS Compustat Global 데이터를 사용하여 계산한 월별 데이터입니다.

---

## 📊 Available Data | 제공 데이터

- **Period**: October 2020 - October 2025 (45 months)
- **Factors**: Market Premium (MKT), Size Premium (SMB), Value Premium (HML), Risk-Free Rate (RF)
- **Frequency**: Monthly
- **Universe**: All Korean stocks in WRDS Compustat Global
- **Methodology**: Fama and French (1993)

**기간**: 2020년 10월 - 2025년 10월 (45개월)  
**팩터**: 시장 프리미엄(MKT), 규모 프리미엄(SMB), 가치 프리미엄(HML), 무위험 이자율(RF)  
**빈도**: 월별  
**대상**: WRDS Compustat Global의 모든 한국 주식  
**방법론**: Fama and French (1993)

---

## 🚀 Quick Start | 빠른 시작

### Download Data | 데이터 다운로드

```python
import pandas as pd

# Load all monthly factors
factors = pd.read_csv('data/monthly_factors.csv', parse_dates=['date'])
print(factors.head())

# Output:
#         date       MKT       SMB       HML        RF
# 0 2020-10-31 -1.947535  0.247685  1.430407  0.083333
# 1 2020-11-30 15.222940  0.587119 -0.745162  0.083333
# ...
```

### Use in Research | 연구에 활용

```python
import pandas as pd
import statsmodels.api as sm

# Load factors
factors = pd.read_csv('data/monthly_factors.csv', parse_dates=['date'])
factors = factors.set_index('date')

# Your stock returns (example)
stock_returns = pd.Series([...], index=factors.index)

# Run Fama-French regression
y = stock_returns - factors['RF']
X = factors[['MKT', 'SMB', 'HML']]
X = sm.add_constant(X)

model = sm.OLS(y, X).fit()
print(model.summary())
```

---

## 📁 Data Files | 데이터 파일

### Monthly Factors | 월별 팩터
- `data/monthly_factors.csv` - Complete dataset (2020-10 to 2025-10)
- `data/2025/factors_2025_01.csv` - January 2025
- `data/2025/factors_2025_02.csv` - February 2025
- ... (individual monthly files)

### Data Format | 데이터 형식

| Column | Description | 설명 |
|--------|-------------|------|
| `date` | Month-end date | 월말 날짜 |
| `MKT` | Market premium (%) | 시장 프리미엄 (%) |
| `SMB` | Size premium (%) | 규모 프리미엄 (%) |
| `HML` | Value premium (%) | 가치 프리미엄 (%) |
| `RF` | Risk-free rate (%) | 무위험 이자율 (%) |

---

## 📈 Factor Statistics | 팩터 통계 (2020-10 to 2025-10)

| Factor | Mean (Monthly) | Std Dev | Min | Max |
|--------|----------------|---------|-----|-----|
| **MKT** | 1.68% | 5.90% | -12.93% | 15.22% |
| **SMB** | 0.45% | 3.07% | -9.43% | 5.88% |
| **HML** | -0.98% | 4.06% | -10.06% | 6.99% |

---

## 🔬 Methodology | 방법론

### Portfolio Formation | 포트폴리오 구성

Following Fama and French (1993):

1. **Size Breakpoint**: Median market capitalization
2. **Value Breakpoints**: 30th and 70th percentile of Book-to-Market ratio
3. **Six Portfolios**: S/L, S/M, S/H, B/L, B/M, B/H
4. **Rebalancing**: Annual (every June)
5. **Weighting**: Value-weighted within portfolios

Fama and French (1993) 방법론:

1. **규모 기준**: 시가총액 중앙값
2. **가치 기준**: Book-to-Market 비율의 30%, 70% 분위수
3. **6개 포트폴리오**: S/L, S/M, S/H, B/L, B/M, B/H
4. **리밸런싱**: 연 1회 (매년 6월)
5. **가중치**: 포트폴리오 내 시가총액 가중

### Factor Calculation | 팩터 계산

```
SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
HML = (S/L + B/L)/2 - (S/H + B/H)/2
MKT = Value-weighted market return - RF
```

### Data Source | 데이터 출처

- **Stock Data**: WRDS Compustat Global (comp.g_secd)
- **Fundamentals**: WRDS Compustat Global (comp.g_funda)
- **Risk-Free Rate**: Korean 3-month treasury rate proxy (1% annual)

**주식 데이터**: WRDS Compustat Global (comp.g_secd)  
**재무제표**: WRDS Compustat Global (comp.g_funda)  
**무위험 이자율**: 한국 3개월 국고채 대용 (연 1%)

---

## 💻 Code | 코드

### Calculate Factors Yourself | 직접 계산하기

```python
from src.korea_factor_calculator import KoreaFactorCalculator
import wrds

# Connect to WRDS
conn = wrds.Connection()

# Initialize calculator
calculator = KoreaFactorCalculator(conn, risk_free_rate=0.01/12)

# Calculate factors for a period
factors = calculator.calculate_factors_for_period('2025-01-01', '2025-09-30')

# Save results
calculator.save_factors(factors, 'my_factors.csv')

conn.close()
```

See `examples/example_usage.py` for more examples.

---

## 📚 Documentation | 문서

- [Methodology](docs/METHODOLOGY.md) - Detailed calculation methodology
- [Data Dictionary](docs/DATA_DICTIONARY.md) - Complete data description
- [Usage Guide](docs/USAGE_GUIDE.md) - How to use the data

**문서**:
- [방법론](docs/METHODOLOGY.md) - 상세한 계산 방법
- [데이터 사전](docs/DATA_DICTIONARY.md) - 완전한 데이터 설명
- [사용 가이드](docs/USAGE_GUIDE.md) - 데이터 사용 방법

---

## 🔄 Updates | 업데이트

Factors are updated monthly, typically on the 5th of each month after month-end data becomes available.

팩터는 매월 5일경 업데이트됩니다 (월말 데이터 확보 후).

### Latest Update | 최근 업데이트
- **Date**: 2025-10-31
- **Period**: October 2025
- **Factors**: MKT=11.06%, SMB=-9.43%, HML=5.74%

---

## 📖 Citation | 인용

If you use this data in your research, please cite:

```bibtex
@misc{korea_ff_factors_2025,
  author = {Your Name},
  title = {Korean Fama-French Three Factors},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/YOUR_USERNAME/korea-fama-french-factors}
}
```

---

## 🤝 Contributing | 기여

Contributions are welcome! Please feel free to submit a Pull Request.

기여를 환영합니다! Pull Request를 자유롭게 제출해주세요.

### How to Contribute | 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License | 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 🙏 Acknowledgments | 감사의 말

- Kenneth R. French for the original Fama-French factors methodology
- WRDS (Wharton Research Data Services) for providing the data
- Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics*, 33(1), 3-56.

---

## 📧 Contact | 연락처

For questions or suggestions, please open an issue or contact:
- Email: your.email@example.com
- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)

질문이나 제안사항이 있으시면 이슈를 열거나 연락주세요.

---

## ⚠️ Disclaimer | 면책조항

This data is provided for academic and research purposes only. The authors make no warranties about the accuracy or completeness of the data. Use at your own risk.

이 데이터는 학술 및 연구 목적으로만 제공됩니다. 데이터의 정확성이나 완전성에 대해 보증하지 않습니다. 사용에 따른 책임은 사용자에게 있습니다.

---

**Last Updated**: 2025-10-31  
**Version**: 1.0.0

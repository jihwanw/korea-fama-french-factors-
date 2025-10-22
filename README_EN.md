# Korea Fama-French Three Factors

Monthly Fama-French 3 Factor data for Korean stock market (Oct 2020 - Oct 2025)

[![Data](https://img.shields.io/badge/Data-WRDS%20Compustat-blue)](https://wrds-www.wharton.upenn.edu/)
[![RF](https://img.shields.io/badge/RF-BOK%20ECOS-green)](https://ecos.bok.or.kr/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)
[![R](https://img.shields.io/badge/R-4.0+-red)](https://www.r-project.org/)

[한국어](README.md) | **English**

---

## 📊 Data

### File Structure
```
korea-fama-french-factors/
├── README.md                          # Korean documentation
├── README_EN.md                       # English documentation
├── data/
│   └── korea_factors_monthly.csv      # Monthly 3 Factor data (MKT, SMB, HML, RF)
├── docs/
│   ├── DATA_COLLECTION_WRDS.md        # WRDS data collection guide
│   └── DATA_COLLECTION_ECOS.md        # ECOS API usage guide
├── korea_factor_calculator.py         # Factor calculation logic
├── korea_factor_updater.py            # Automatic factor updater
├── korea_rf_fetcher.py                # Risk-free rate fetcher
├── korea_ticker_utils.py              # WRDS data query utilities
└── fama_macbeth_test.py               # Fama-MacBeth regression test
```

### Python Scripts

| File | Description | Purpose |
|------|-------------|----------|
| **korea_factor_calculator.py** | Fama-French 3 Factor calculator | Portfolio formation and factor calculation |
| **korea_factor_updater.py** | Automatic factor updater | Detect missing months and calculate |
| **korea_rf_fetcher.py** | Risk-free rate fetcher | Fetch data from BOK ECOS API |
| **korea_ticker_utils.py** | WRDS data utilities | Query stock prices, market cap, book equity |
| **fama_macbeth_test.py** | Fama-MacBeth regression test | Test factor significance and statistics |

### Data Format
```csv
date,MKT,SMB,HML,RF
2020-10-31,-1.95,0.25,1.43,0.057
2020-11-30,15.22,0.59,-0.75,0.058
...
```

### Variable Descriptions
| Variable | Description | Unit |
|----------|-------------|------|
| **date** | Month-end date | YYYY-MM-DD |
| **MKT** | Market Premium = Market Return - RF | % |
| **SMB** | Small Minus Big = Small - Large cap | % |
| **HML** | High Minus Low = Value - Growth | % |
| **RF** | Risk-Free Rate = 1-year treasury / 12 | % |

---

## 🔬 Methodology

### Fama-French 3 Factor Model (1993)

#### Step 1: Portfolio Formation (2x3 Sort)

**Size Classification** (Market Cap)
- Small (S): Below median
- Big (B): Above median

**Value Classification** (Book-to-Market)
- Low (L): Top 30% (Value)
- Medium (M): Middle 40%
- High (H): Bottom 30% (Growth)

**6 Portfolios**: S/L, S/M, S/H, B/L, B/M, B/H

#### Step 2: Factor Calculation

```
SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
HML = (S/L + B/L)/2 - (S/H + B/H)/2
MKT = Value-weighted market return - RF
```

---

## 📥 Data Sources

### 1. Stock Prices & Market Cap

**Source**: WRDS Compustat Global Security Daily

**Access**: 
- WRDS account required: https://wrds-www.wharton.upenn.edu/
- Institutional subscription needed

**Database**: `comp.g_secd`

**Fields**:
- `prccd`: Closing Price
- `ajexdi`: Adjustment Factor
- `cshoc`: Shares Outstanding
- `market_cap = prccd / ajexdi * cshoc`

**Guide**: [docs/DATA_COLLECTION_WRDS.md](docs/DATA_COLLECTION_WRDS.md)

---

### 2. Book Equity

**Source**: WRDS Compustat Global Fundamentals Annual

**Database**: `comp.g_funda`

**Fields**:
- `ceq`: Common Equity
- Most recent annual data used

---

### 3. Risk-Free Rate

**Source**: Bank of Korea Economic Statistics System (ECOS)

**API Access**:
1. Get API key: https://ecos.bok.or.kr/
2. Stat Code: `817Y002` (1-year Korea treasury bond)
3. Item Code: `010190000`
4. Frequency: Daily → Monthly average
5. Conversion: Annual rate / 12 = Monthly rate

**Guide**: [docs/DATA_COLLECTION_ECOS.md](docs/DATA_COLLECTION_ECOS.md)

---

## 💻 Usage

### Python

```python
import pandas as pd

# Load data
factors = pd.read_csv('data/korea_factors_monthly.csv', parse_dates=['date'])

# View summary
print(factors.describe())
print(factors.tail())

# Calculate cumulative returns
factors['MKT_cum'] = (1 + factors['MKT']/100).cumprod() - 1
```

### R

```r
# Load data
factors <- read.csv('data/korea_factors_monthly.csv')
factors$date <- as.Date(factors$date)

# View summary
summary(factors)
tail(factors)

# Calculate cumulative returns
factors$MKT_cum <- cumprod(1 + factors$MKT/100) - 1

# Plot
library(ggplot2)
ggplot(factors, aes(x=date, y=MKT)) +
  geom_line() +
  labs(title="Korea Market Premium", y="Return (%)")
```

---

## 🔄 Data Update

### Update Risk-Free Rate
```bash
python korea_rf_fetcher.py --config config.json
```

### Recalculate Factors
```bash
python korea_factor_updater.py --filepath data/korea_factors_monthly.csv
```

### Test Factor Significance
```bash
python fama_macbeth_test.py
```

---

## 📚 References

1. **Fama, E. F., & French, K. R. (1993)**  
   "Common risk factors in the returns on stocks and bonds"  
   *Journal of Financial Economics*, 33(1), 3-56.  
   DOI: 10.1016/0304-405X(93)90023-5

2. **WRDS Compustat Global**  
   Wharton Research Data Services  
   https://wrds-www.wharton.upenn.edu/

3. **Bank of Korea ECOS**  
   Economic Statistics System  
   https://ecos.bok.or.kr/

---

## 📄 License

Academic Research Use Only

---

## 📞 Contact

- GitHub: [@jihwanw](https://github.com/jihwanw)
- Repository: [korea-fama-french-factors](https://github.com/jihwanw/korea-fama-french-factors-)

---

**Last Updated**: 2025-10-22  
**Data Period**: 2020-10-31 to 2025-10-31 (61 months)  
**RF Source**: Bank of Korea ECOS API (Stat: 817Y002)

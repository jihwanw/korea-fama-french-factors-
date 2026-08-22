# Korea Fama-French Factors Library (FF5 + Momentum)

**Monthly factor returns for the Korean stock market, July 2001 – present. Updated monthly. The Korean analog of the Ken French Data Library.**

[![Data](https://img.shields.io/badge/Data-WRDS%20Compustat%20Global-blue)](https://wrds-www.wharton.upenn.edu/)
[![RF](https://img.shields.io/badge/RF-BOK%20ECOS-green)](https://ecos.bok.or.kr/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22059320.svg)](https://doi.org/10.5281/zenodo.22059320)
[![Factors](https://img.shields.io/badge/Factors-6%20(FF5%2BWML)-orange)]()

[한국어](README.md) | **English**

---

## What This Repository Provides

- **6 monthly factors** (2001-07 – present, 302+ months): `MKT_RF` `SMB` `HML` `RMW` `CMA` `WML`
- **Fully reproducible pipeline**: from raw data pull to factor construction
- **Proof of implementation**: the same code replicates the official US French factors (corr 0.96–0.999)
- **Monthly automated updates** with per-version DOIs for academic citation

## Quick Start

```python
import pandas as pd
url = "https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors-/main/data/factors_monthly_kr_ff5.csv"
factors = pd.read_csv(url, index_col=0)   # units: % per month
```

More examples in [`examples/`](examples/), including a Fama-MacBeth regression tutorial.

## New to Factors? A 3-Minute Primer

Each factor is the return of a hypothetical portfolio that buys stocks with one trait and sells stocks with the opposite trait:

| Factor | Long / Short | Intuition |
|---|---|---|
| MKT_RF | market / risk-free | reward for holding stocks |
| SMB | small caps / large caps | do small firms earn more? |
| HML | value / growth | do cheap firms earn more? |
| RMW | profitable / unprofitable | does profitability pay? |
| CMA | conservative / aggressive investment | does restraint pay? |
| WML | recent winners / losers | do winners keep winning? |

Use cases: fund performance evaluation (alpha), anomaly research, asset-pricing tests, risk decomposition.

## Can You Trust This Code? — Proven on US Data

Factor construction involves dozens of subtle decisions. Instead of claiming correctness, we **proved it experimentally**: applying this exact pipeline to US CRSP/Compustat data reproduces the officially published Fama-French factors.

**Results** (1995-07 – 2024-12, 354 months, [`src/us_replication.py`](src/us_replication.py)):

| Factor | Correlation with official French factors |
|---|---|
| MKT | **0.9992** |
| SMB | **0.9930** |
| HML | **0.9612** |
| RMW | **0.9615** |
| CMA | **0.9713** |

These match the benchmarks of published replication studies. The Korean factors are therefore *verified logic + Korean data*. Full audit: [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md)

## Adapting to Korea: Key Assumptions

1. **KOSPI plays the role of NYSE** — breakpoints use KOSPI stocks only; KOSDAQ stocks are then classified by those breakpoints (mirroring the NYSE/NASDAQ convention).
2. **Risk-free rate = 91-day CD rate** (Bank of Korea ECOS) — the standard proxy in Korean empirical research.
3. **Annual rebalancing at end of June** — Korean firms are predominantly December fiscal-year-end with annual reports due by end of March, so June leaves a 3-month safety lag against look-ahead bias (same timing as FF).
4. **Delisted stocks included** (no survivorship bias) — performance-related delistings receive a −30% delisting return (Shumway 1997); mergers are not adjusted. Sensitivity analysis: impact ≤1.2bp/month on all factors.
5. **Book equity = CEQ** (common equity) — the practical K-IFRS approximation of FF's SEQ+TXDITC−PS; documented as a simplification in [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).
6. **Market factor validated**: correlation 0.994 with the KOSPI index; crisis months (Oct 2008, Mar 2020) captured exactly. Full validation: [`docs/VALIDATION.md`](docs/VALIDATION.md)

## Known Limitations

- These are *academic constructs*, not tradable strategies (no transaction costs, shorting constraints, or liquidity limits).
- CMA is statistically insignificant in Korea (as in many non-US markets) — provided, but interpret with care.
- Factors (aggregated derivatives) are public; reproducing them requires your own WRDS license for raw data.

## Citation

> Woo, Jihwan. *Korea Fama-French Factors (FF5 + Momentum)* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.22059320

Use the Concept DOI above for general citation; cite a release-specific Version DOI for exact reproducibility. BibTeX available via GitHub's "Cite this repository" button.

## Related Repositories

- [fama-french-3factor](https://github.com/jihwanw/fama-french-3factor) — US FF3 implementation (DOI: 10.5281/zenodo.18883631)
- [fama-french-5factor](https://github.com/jihwanw/fama-french-5factor) — US FF5 implementation (DOI: 10.5281/zenodo.18883752)

## License & Disclaimer

Code: MIT · Data: CC-BY-4.0. Provided for research and education; not investment advice.

## Author

**Jihwan Woo** — Ph.D., AI/Finance researcher · [Homepage](https://jihwanw.github.io/) · [ORCID 0000-0002-0424-0242](https://orcid.org/0000-0002-0424-0242)

Issues and PRs welcome. If this repository helps your research, please star and fork.

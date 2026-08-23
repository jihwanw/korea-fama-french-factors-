# 한국 주식시장 Fama-French 팩터 라이브러리 (FF5 + Momentum)

**2001년 7월 ~ 현재, 매월 자동 갱신되는 한국판 Ken French Data Library**

[![Data](https://img.shields.io/badge/Data-WRDS%20Compustat%20Global-blue)](https://wrds-www.wharton.upenn.edu/)
[![RF](https://img.shields.io/badge/RF-BOK%20ECOS-green)](https://ecos.bok.or.kr/)
[![Factors](https://img.shields.io/badge/Factors-6%20(FF5%2BWML)-orange)]()
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22059320.svg)](https://doi.org/10.5281/zenodo.22059320)
[![Months](https://img.shields.io/badge/Coverage-2001--07%20~%20now-brightgreen)]()

**한국어** | [English](README_EN.md)

---

## 이 저장소가 제공하는 것

미국에는 [Ken French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)가 있어 누구나 무료로 팩터 데이터를 받아 연구할 수 있습니다. 한국에는 그런 공개 라이브러리가 없었습니다. 이 저장소는 그 공백을 채웁니다.

- **6개 팩터 월간 시계열** (2001-07 ~ 현재, 302개월+): `MKT_RF` `SMB` `HML` `RMW` `CMA` `WML`
- **완전한 재현 코드**: 데이터 수집부터 팩터 계산까지 전 과정 공개
- **구현 증명**: 같은 코드로 미국 French 팩터를 재현해 정확성을 검증 (상관 0.96~0.999)
- **매월 자동 갱신** + 버전별 DOI (논문 인용 가능)

```csv
month,MKT_RF,SMB,HML,RMW,CMA,WML,RF,MKT
2001-07,-4.7057,1.0157,2.7511,...
...
2026-08,,0.27,-2.993,-7.309,-1.143,3.274,,6.631
```

## 빠른 시작

```python
import pandas as pd
url = "https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors-/main/data/factors_monthly_kr_ff5.csv"
factors = pd.read_csv(url, index_col=0, parse_dates=False)
print(factors.tail())      # 단위: % (월간)
```

```r
factors <- read.csv("https://raw.githubusercontent.com/jihwanw/korea-fama-french-factors-/main/data/factors_monthly_kr_ff5.csv")
tail(factors)
```

더 많은 예제: [`examples/`](examples/) — 포트폴리오 초과수익률 회귀, Fama-MacBeth 검정 실습 포함.

---

## 팩터가 처음이라면: 3분 설명

주식 수익률은 왜 종목마다 다를까요? Fama와 French는 수익률 차이의 상당 부분이 몇 가지 **공통 요인(팩터)**으로 설명된다는 것을 보였습니다. 각 팩터는 "특정 성질을 가진 주식을 사고, 반대 성질의 주식을 파는 가상의 포트폴리오"의 수익률입니다.

| 팩터 | 읽는 법 | 사는 것 / 파는 것 | 직관 |
|---|---|---|---|
| MKT_RF | 시장 | 주식시장 전체 / 무위험자산 | "주식을 들고 있는 대가" |
| SMB | Small Minus Big | 소형주 / 대형주 | "작은 회사가 더 벌까?" |
| HML | High Minus Low | 가치주(장부가/시가 높음) / 성장주 | "싸게 거래되는 회사가 더 벌까?" |
| RMW | Robust Minus Weak | 고수익성 기업 / 저수익성 기업 | "돈 잘 버는 회사가 더 벌까?" |
| CMA | Conservative Minus Aggressive | 투자 보수적 기업 / 공격적 기업 | "몸집 불리기에 신중한 회사가 더 벌까?" |
| WML | Winners Minus Losers | 최근 1년 상승주 / 하락주 | "오르던 주식이 계속 오를까?" |

이 데이터로 할 수 있는 것: 펀드 성과 평가(알파 측정), 이상현상(anomaly) 연구, 자산가격결정 모형 검정, 포트폴리오 리스크 분해 — 즉 실증 재무 연구의 기본 재료입니다.

---

## 이 코드를 믿어도 되나요? — 미국 데이터로 증명했습니다

팩터 구축에는 수십 개의 세부 결정이 필요하고, 하나만 틀려도 결과가 달라집니다. "우리 구현이 Fama-French 명세 그대로"라는 주장을 **실험으로 증명**했습니다.

> **아이디어**: Fama-French는 미국 팩터의 정답지를 매달 공개한다. 우리 코드를 미국 데이터(CRSP/Compustat)에 적용해서 그 정답지가 재현되면, 코드가 옳다는 뜻이다.

**결과** (1995-07 ~ 2024-12, 354개월, [`src/us_replication.py`](src/us_replication.py)):

| 팩터 | 자체 구현 vs French 공식 상관계수 |
|---|---|
| MKT | **0.9992** |
| SMB | **0.9930** |
| HML | **0.9612** |
| RMW | **0.9615** |
| CMA | **0.9713** |

학술 재현 연구들의 벤치마크(SMB ~0.99, HML ~0.96)와 같은 수준입니다. 즉, **소트·브레이크포인트·가중·공식 로직이 FF 명세대로 작동함이 검증**되었고, 한국 팩터는 "검증된 코드 + 한국 데이터"입니다. 상세 감사표: [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md)

---

## 한국 시장 적용: 무엇을 가정했고 왜 그랬나

미국 방법론을 한국에 그대로 옮길 수는 없습니다. 우리가 내린 결정들과 그 이유입니다 (초심자용 비유 포함):

**1. KOSPI가 NYSE 역할을 합니다 (브레이크포인트)**
FF는 "대형/소형"의 기준선을 NYSE 종목만으로 정합니다. NASDAQ의 수많은 초소형주가 기준을 왜곡하지 않게 하기 위해서입니다. 한국의 유사 구조는 KOSPI(본장)와 KOSDAQ이므로, **기준선은 KOSPI 종목만으로** 정하고 KOSDAQ 종목을 그 기준에 따라 분류합니다.

**2. 무위험수익률은 CD 91일 금리입니다**
미국은 1개월 T-bill을 쓰지만 한국에는 그에 정확히 대응하는 초단기 국채 시계열이 없습니다. 한국 실증 연구의 관행대로 **CD(91일) 금리**(한국은행 ECOS)를 월 단위로 환산해 사용합니다.

**3. 리밸런싱은 매년 6월 말입니다**
작년 재무제표가 시장에 공시된 후에만 사용해야 합니다(미래 정보 금지, look-ahead bias 방지). 한국 상장사 대부분은 12월 결산이고 사업보고서는 3월 말까지 제출되므로, 6월 말 리밸런싱은 **최소 3개월의 안전 여유**를 둔 선택입니다 (FF 원전과 동일한 시점).

**4. 상장폐지 주식도 포함합니다 (생존 편향 제거)**
"지금 살아남은 종목"만으로 과거를 계산하면 수익률이 부풀려집니다(생존 편향). 우리 데이터는 **상장폐지된 기업을 포함**하며, 부실 상폐 종목에는 마지막 거래 다음 달 **-30% 수익률**을 부여합니다(Shumway 1997의 학술 표준). 합병으로 사라진 종목은 주주가 대가를 받으므로 조정하지 않습니다. 민감도 분석 결과 이 조정이 팩터에 주는 영향은 월 0.012%p 이하로 미미하지만, 원칙의 문제이므로 적용합니다.

**5. 장부가치는 보통주 자본(CEQ)입니다**
FF의 미국 정의는 "자본총계 + 이연법인세 − 우선주"인데, 한국(K-IFRS) 데이터에서는 **보통주 자본(CEQ)**이 그에 가장 가까운 실용적 근사입니다. 이연법인세 가산을 생략한 단순화이며, 이런 이탈은 전부 [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md)에 명시했습니다.

**6. 검증: 시장 팩터가 진짜 시장을 따라가나?**
자체 계산한 시장수익률과 KOSPI 지수의 상관은 **0.994**입니다. 2008년 10월(금융위기 −24%), 2020년 3월(COVID −11%) 같은 사건들도 정확히 잡힙니다. 전체 검증: [`docs/VALIDATION.md`](docs/VALIDATION.md)

---

## 알려진 한계 (정직하게)

- **투자 전략이 아닙니다**: 팩터는 거래비용·공매도 제약·유동성을 무시한 *학술적 구성물*입니다. 특히 소형주 기반 수익률은 실제로 얻기 어렵습니다.
- **CMA는 비유의**: 한국에서 투자 팩터는 통계적으로 유의하지 않습니다(국제적으로도 가장 약한 팩터). 데이터는 제공하되 해석에 주의하세요.
- **원천 데이터 접근**: 팩터(집계 파생물)는 공개하지만, 원천 데이터(WRDS)는 각자 라이선스로 접근해야 재현할 수 있습니다.
- 상세: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) §6

## 인용 방법

논문에서 이 데이터를 사용하실 때:

> Woo, Jihwan. *Korea Fama-French Factors (FF5 + Momentum)* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.22059320

- **Concept DOI**(위)는 항상 최신 버전을 가리킵니다 — 일반적 인용에 권장
- 특정 월 버전의 재현이 필요하면 해당 릴리스의 **Version DOI**를 인용하세요
- GitHub의 "Cite this repository" 버튼으로 BibTeX을 받을 수 있습니다
- 라이브러리를 소개하는 워킹페이퍼: [SSRN 7339600](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7339600) · [PDF (repo 사본)](paper/main.pdf)

## 갱신 주기

매월 초(전월 데이터 확정 후) 자동 갱신되며, 갱신마다 새 릴리스와 Version DOI가 발급됩니다. `MKT_RF`와 `RF`는 한국은행 CD금리 공표 일정에 따라 1개월 정도 늦게 채워질 수 있습니다.

## 저장소 구조

```
data/       팩터 CSV (메인: factors_monthly_kr_ff5.csv)
docs/       방법론·검증·준수 감사·데이터 수집 가이드
src/        팩터 구축·검증·미국 재현·월간 갱신 코드
examples/   pandas/R 로드, Fama-MacBeth 검정 실습
```

## 관련 저장소

- [fama-french-3factor](https://github.com/jihwanw/fama-french-3factor) — 미국 FF3 구현 (DOI: 10.5281/zenodo.18883631)
- [fama-french-5factor](https://github.com/jihwanw/fama-french-5factor) — 미국 FF5 구현 (DOI: 10.5281/zenodo.18883752)

## 라이선스와 면책

- 코드: MIT · 데이터: CC-BY-4.0 (인용 조건 재사용 가능)
- 본 데이터는 연구·교육 목적으로 제공되며 투자 조언이 아닙니다. 정확성을 위해 노력했으나 오류가 있을 수 있고, 사용에 따른 책임은 사용자에게 있습니다.

## 만든 사람

**우지환 (Jihwan Woo)** — Ph.D., AI/금융 연구자 · [홈페이지](https://jihwanw.github.io/) · [ORCID 0000-0002-0424-0242](https://orcid.org/0000-0002-0424-0242)

질문·오류 제보는 [Issues](../../issues)로, 개선 기여는 PR로 환영합니다. 이 저장소가 유용했다면 Star와 Fork 부탁드립니다.

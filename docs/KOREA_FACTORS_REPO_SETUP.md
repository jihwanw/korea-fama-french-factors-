# 한국 Fama-French 팩터 GitHub 저장소 설정 가이드

## 1. GitHub에서 새 저장소 만들기

1. GitHub 웹사이트 접속: https://github.com
2. 우측 상단 "+" 클릭 → "New repository"
3. 저장소 정보 입력:
   - **Repository name**: `korea-fama-french-factors`
   - **Description**: "Monthly Fama-French Three Factors for Korean Stock Market (한국 주식시장 Fama-French 3 팩터 월별 데이터)"
   - **Public** 선택 (학계 공유용)
   - **Add README file** 체크
   - **Add .gitignore**: Python 선택
   - **Choose a license**: MIT License 추천
4. "Create repository" 클릭

## 2. 로컬에 저장소 클론

```bash
# 터미널에서 실행
cd ~/Desktop/projects
git clone https://github.com/YOUR_USERNAME/korea-fama-french-factors.git
cd korea-fama-french-factors
```

## 3. 현재 프로젝트에서 파일 복사

```bash
# 현재 finance-research 프로젝트에서 필요한 파일 복사
cd ~/Desktop/projects/development/agentcore

# 팩터 계산 코드 복사
cp korea_factor_calculator.py ~/Desktop/projects/korea-fama-french-factors/src/
cp korea_ticker_utils.py ~/Desktop/projects/korea-fama-french-factors/src/

# 팩터 데이터 복사
cp data/korea_factors_monthly.csv ~/Desktop/projects/korea-fama-french-factors/data/monthly_factors.csv

# WRDS 설정 파일 복사 (주의: 민감 정보 제거 필요)
# wrds_config.json은 복사하지 않음 (개인 정보)
```

## 4. 필요한 파일 생성

아래 명령어로 이 가이드에서 생성할 파일들을 만듭니다:

```bash
cd ~/Desktop/projects/korea-fama-french-factors

# 디렉토리 구조 생성
mkdir -p src data/2025 docs examples

# 파일 생성 (아래 섹션 참조)
```

## 5. README.md 작성

저장소의 메인 README.md 파일을 작성합니다 (다음 섹션 참조).

## 6. 2025년 1-9월 데이터 추출

현재 `data/korea_factors_monthly.csv`에서 2025년 데이터를 추출합니다:

```python
import pandas as pd

# 전체 데이터 로드
df = pd.read_csv('data/korea_factors_monthly.csv', parse_dates=['date'])

# 2025년 데이터만 필터링
df_2025 = df[df['date'].dt.year == 2025]

# 월별로 저장
for idx, row in df_2025.iterrows():
    month = row['date'].month
    filename = f"data/2025/factors_2025_{month:02d}.csv"
    row_df = pd.DataFrame([row])
    row_df.to_csv(filename, index=False)
    print(f"Saved: {filename}")

print(f"\n✅ {len(df_2025)}개월 데이터 저장 완료!")
```

## 7. Git 커밋 및 푸시

```bash
cd ~/Desktop/projects/korea-fama-french-factors

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: Korean Fama-French Three Factors

- Add factor calculation code
- Add monthly factor data (2020-10 to 2025-10)
- Add 2025 monthly data files (Jan-Sep)
- Add documentation and examples"

# GitHub에 푸시
git push origin main
```

## 8. GitHub 저장소 설정

### Topics 추가
저장소 페이지에서 "Add topics" 클릭:
- `fama-french`
- `factor-models`
- `korean-stock-market`
- `asset-pricing`
- `finance`
- `quantitative-finance`

### About 섹션 업데이트
- Website: (있다면 추가)
- Description: "Monthly Fama-French Three Factors for Korean Stock Market"

### README 뱃지 추가
```markdown
![Data Updated](https://img.shields.io/badge/Data%20Updated-2025--10-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
```

## 9. 월별 자동 업데이트 설정 (선택사항)

GitHub Actions를 사용하여 매월 자동 업데이트:

`.github/workflows/update_factors.yml` 파일 생성:

```yaml
name: Update Monthly Factors

on:
  schedule:
    - cron: '0 0 5 * *'  # 매월 5일 자정 실행
  workflow_dispatch:  # 수동 실행 가능

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Update factors
        env:
          WRDS_USERNAME: ${{ secrets.WRDS_USERNAME }}
          WRDS_PASSWORD: ${{ secrets.WRDS_PASSWORD }}
        run: |
          python src/update_factors.py
      - name: Commit and push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/
          git commit -m "Update factors for $(date +'%Y-%m')" || exit 0
          git push
```

## 10. 홍보 및 공유

1. **학계 공유**
   - 관련 교수님들께 이메일
   - 학회 메일링 리스트

2. **온라인 커뮤니티**
   - Reddit: r/algotrading, r/quant
   - Twitter/X: #QuantFinance #FamaFrench
   - LinkedIn

3. **논문 인용**
   - 논문에 데이터 출처로 명시
   - DOI 발급 (Zenodo 사용)

## 다음 단계

이제 아래 파일들을 생성하겠습니다:
1. README.md (메인 소개)
2. METHODOLOGY.md (계산 방법론)
3. update_factors.py (월별 업데이트 스크립트)
4. example_usage.py (사용 예제)

계속 진행하시겠습니까?

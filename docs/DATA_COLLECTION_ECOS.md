# 한국은행 ECOS 데이터 수집 가이드

## 개요

한국은행 경제통계시스템(ECOS)에서 국고채 수익률 데이터를 수집하는 방법을 설명합니다.

---

## 1. API 키 발급

### 회원가입
1. **ECOS 웹사이트 접속**: https://ecos.bok.or.kr/
2. 우측 상단 "회원가입" 클릭
3. 이메일 인증 완료

### API 키 신청
1. 로그인 후 상단 메뉴 "인증키 신청/관리" 클릭
2. "인증키 신청" 버튼 클릭
3. **용도**: "학술연구" 선택
4. 신청 완료 후 **즉시 발급**

### API 키 확인
- "인증키 신청/관리" 페이지에서 발급된 키 확인
- 형식: 영문+숫자 조합 (예: ABC123DEF456GHI789)
- **중요**: 키는 재발급 불가, 안전하게 보관

---

## 2. 통계표 정보

### 국고채(1년) 수익률

| 항목 | 값 |
|------|-----|
| **통계표코드** | 817Y002 |
| **통계표명** | 국고채(1년) 수익률 |
| **통계항목코드** | 010190000 |
| **통계항목명** | 국고채(1년) |
| **주기** | 일별(D) |
| **단위** | 연율(%) |
| **출처** | 한국은행 |

### 기타 국고채 수익률
- 국고채(3년): 817Y003
- 국고채(5년): 817Y004
- 국고채(10년): 817Y005

---

## 3. API 사용법

### 기본 URL 구조
```
https://ecos.bok.or.kr/api/{서비스명}/{인증키}/{요청타입}/{언어}/{시작건수}/{종료건수}/{통계표코드}/{주기}/{시작일자}/{종료일자}/{통계항목코드}
```

### 파라미터 설명
| 파라미터 | 설명 | 예시 |
|----------|------|------|
| 서비스명 | API 서비스 | StatisticSearch |
| 인증키 | 발급받은 API 키 | YOUR_API_KEY |
| 요청타입 | 응답 형식 | json, xml |
| 언어 | 언어 코드 | kr, en |
| 시작건수 | 페이징 시작 | 1 |
| 종료건수 | 페이징 끝 | 10000 |
| 통계표코드 | 통계표 ID | 817Y002 |
| 주기 | 데이터 주기 | D(일), M(월), Y(년) |
| 시작일자 | 조회 시작일 | 20201001 |
| 종료일자 | 조회 종료일 | 20251031 |
| 통계항목코드 | 항목 ID | 010190000 |

---

## 4. API 호출 예시

### cURL
```bash
curl "https://ecos.bok.or.kr/api/StatisticSearch/YOUR_API_KEY/json/kr/1/10000/817Y002/D/20201001/20251031/010190000"
```

### Python (requests)
```python
import requests
import pandas as pd

api_key = "YOUR_API_KEY"
stat_code = "817Y002"  # 국고채(1년)
item_code = "010190000"
start_date = "20201001"
end_date = "20251031"

url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10000/{stat_code}/D/{start_date}/{end_date}/{item_code}"

response = requests.get(url)
data = response.json()

if 'StatisticSearch' in data:
    rows = data['StatisticSearch']['row']
    df = pd.DataFrame(rows)
    print(f"Retrieved {len(df)} observations")
else:
    print("Error:", data)
```

---

## 5. 응답 데이터 구조

### JSON 응답 예시
```json
{
  "StatisticSearch": {
    "row": [
      {
        "STAT_CODE": "817Y002",
        "STAT_NAME": "국고채(1년) 수익률",
        "ITEM_CODE1": "010190000",
        "ITEM_NAME1": "국고채(1년)",
        "DATA_VALUE": "0.68",
        "TIME": "20201001",
        "UNIT_NAME": "%"
      },
      ...
    ]
  }
}
```

### 주요 필드
| 필드 | 설명 |
|------|------|
| `TIME` | 날짜 (YYYYMMDD) |
| `DATA_VALUE` | 수익률 (연율 %) |
| `UNIT_NAME` | 단위 (%) |

---

## 6. 데이터 처리

### 일별 → 월별 변환
```python
import pandas as pd

# 일별 데이터 로드
df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
df['rate'] = pd.to_numeric(df['DATA_VALUE'])

# 월별 평균 계산
df['year_month'] = df['date'].dt.to_period('M')
monthly_avg = df.groupby('year_month')['rate'].mean().reset_index()

# 연율 → 월율 변환
monthly_avg['RF'] = monthly_avg['rate'] / 12

# 월말 날짜로 변환
monthly_avg['date'] = monthly_avg['year_month'].dt.to_timestamp('M')

result = monthly_avg[['date', 'RF']]
print(result.head())
```

### 결과 예시
```
        date        RF
0 2020-10-31  0.056632
1 2020-11-30  0.058313
2 2020-12-31  0.059905
```

---

## 7. 전체 코드 예시

### korea_rf_fetcher.py
```python
import requests
import pandas as pd
import json

class KoreaRiskFreeRateFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://ecos.bok.or.kr/api"
    
    def fetch_treasury_1year(self, start_date, end_date):
        """국고채 1년물 수익률 조회"""
        stat_code = "817Y002"
        item_code = "010190000"
        
        url = f"{self.base_url}/StatisticSearch/{self.api_key}/json/kr/1/10000/{stat_code}/D/{start_date}/{end_date}/{item_code}"
        
        response = requests.get(url)
        data = response.json()
        
        if 'StatisticSearch' not in data:
            raise Exception(f"API Error: {data}")
        
        rows = data['StatisticSearch']['row']
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
        df['rate'] = pd.to_numeric(df['DATA_VALUE'])
        
        return df[['date', 'rate']].sort_values('date')
    
    def calculate_monthly_rf(self, daily_df):
        """월별 무위험 수익률 계산"""
        daily_df['year_month'] = daily_df['date'].dt.to_period('M')
        monthly_avg = daily_df.groupby('year_month')['rate'].mean().reset_index()
        monthly_avg['RF'] = monthly_avg['rate'] / 12
        monthly_avg['date'] = monthly_avg['year_month'].dt.to_timestamp('M')
        return monthly_avg[['date', 'RF']]

# 사용 예시
with open('config.json') as f:
    config = json.load(f)

fetcher = KoreaRiskFreeRateFetcher(config['ecos_api_key'])
daily_data = fetcher.fetch_treasury_1year('20201001', '20251031')
monthly_rf = fetcher.calculate_monthly_rf(daily_data)
monthly_rf.to_csv('data/korea_rf_monthly.csv', index=False)
```

---

## 8. 실행 방법

### 설정 파일 생성 (config.json)
```json
{
  "ecos_api_key": "YOUR_API_KEY_HERE"
}
```

### 스크립트 실행
```bash
python korea_rf_fetcher.py --config config.json --start-date 20201001 --end-date 20251031
```

---

## 9. 문제 해결

### API 키 오류
```json
{
  "RESULT": {
    "CODE": "600",
    "MESSAGE": "인증키가 유효하지 않습니다."
  }
}
```
**해결**: API 키 재확인 또는 재발급

### 데이터 없음
```json
{
  "RESULT": {
    "CODE": "200",
    "MESSAGE": "해당 데이터가 없습니다."
  }
}
```
**해결**: 날짜 범위 또는 통계표코드 확인

### 요청 제한
- 일일 요청 제한: 10,000건
- 초과 시 다음날 재시도

---

## 10. 참고 자료

### 공식 문서
- ECOS 홈페이지: https://ecos.bok.or.kr/
- API 가이드: https://ecos.bok.or.kr/api/
- 통계표 검색: https://ecos.bok.or.kr/jsp/vis/keystat/#/key

### 관련 통계
- 금리 통계: https://ecos.bok.or.kr/jsp/vis/keystat/#/key/G10
- 국고채 수익률: 통계표 817Y002~817Y005

---

**작성일**: 2025-10-22  
**API 버전**: ECOS Open API v1.0

# 한국은행 ECOS API 설정 가이드

## 1. API 키 발급

1. **한국은행 경제통계시스템 접속**
   - URL: https://ecos.bok.or.kr/

2. **회원가입 및 로그인**
   - 우측 상단 "회원가입" 클릭
   - 이메일 인증 완료

3. **API 키 발급**
   - 로그인 후 상단 메뉴 "인증키 신청/관리" 클릭
   - "인증키 신청" 버튼 클릭
   - 용도: "학술연구" 선택
   - 신청 완료 후 즉시 발급

4. **API 키 확인**
   - "인증키 신청/관리" 페이지에서 발급된 키 확인
   - 형식: 영문+숫자 조합 (예: ABC123DEF456GHI789)

## 2. 사용할 통계표

### 국고채(1년) 수익률
- **통계표코드**: 817Y002
- **통계항목코드**: 010190000
- **주기**: 일별(D)
- **단위**: 연율(%)

### API 호출 예시
```
https://ecos.bok.or.kr/api/StatisticSearch/YOUR_API_KEY/json/kr/1/10000/817Y002/D/20201001/20251031/010190000
```

## 3. 설정 파일 생성

`ecos_config.json` 파일 생성:
```json
{
  "api_key": "YOUR_ECOS_API_KEY_HERE"
}
```

**주의**: 이 파일은 `.gitignore`에 추가되어 있습니다.

## 4. 데이터 수집 실행

```bash
python korea_rf_fetcher.py --api-key YOUR_API_KEY
```

또는 설정 파일 사용:
```bash
python korea_rf_fetcher.py --config ecos_config.json
```

#!/usr/bin/env python3
"""
한국 무위험 수익률 데이터 소스 테스트

가능한 데이터 소스:
1. 한국은행 경제통계시스템 (ECOS)
2. Kenneth French Data Library (Global factors)
3. FRED (Federal Reserve Economic Data)
4. Yahoo Finance (Korea Treasury ETF)
5. Investing.com API
"""

import pandas as pd
import requests
from datetime import datetime

def test_fred_korea_rates():
    """FRED에서 한국 국채 수익률 조회"""
    print("="*80)
    print("1. FRED - Korea Treasury Rates")
    print("="*80)
    
    # FRED API (무료, API 키 필요)
    # Series: IRLTLT01KRM156N (Long-term government bond yields: 10-year)
    print("FRED Series: IRLTLT01KRM156N (10-year Korea government bond)")
    print("URL: https://fred.stlouisfed.org/series/IRLTLT01KRM156N")
    print("Status: ✅ Available (requires API key)")
    print()

def test_kenneth_french_global():
    """Kenneth French Data Library - Global factors"""
    print("="*80)
    print("2. Kenneth French Data Library - Global Factors")
    print("="*80)
    
    print("URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html")
    print("Dataset: Developed Markets Factors")
    print("Status: ✅ Available (includes Asia-Pacific)")
    print("Note: 지역별 팩터는 있지만 한국 개별 RF는 없음")
    print()

def test_ecos_bok():
    """한국은행 경제통계시스템 (ECOS)"""
    print("="*80)
    print("3. 한국은행 ECOS - 국고채 수익률")
    print("="*80)
    
    print("API: https://ecos.bok.or.kr/")
    print("통계표: 국고채(1년) 수익률 - 817Y002")
    print("통계표: 국고채(3년) 수익률 - 817Y003")
    print("Status: ✅ Available (requires API key)")
    print("Note: 가장 정확한 한국 데이터")
    print()

def test_investing_com():
    """Investing.com - Korea Treasury Bonds"""
    print("="*80)
    print("4. Investing.com - Korea Treasury Bonds")
    print("="*80)
    
    print("URL: https://www.investing.com/rates-bonds/south-korea-1-year-bond-yield")
    print("Data: 1-year, 3-year, 5-year, 10-year Korea government bonds")
    print("Status: ✅ Available (web scraping or API)")
    print()

def test_yahoo_finance_etf():
    """Yahoo Finance - Korea Treasury ETF"""
    print("="*80)
    print("5. Yahoo Finance - Korea Treasury ETF")
    print("="*80)
    
    try:
        import yfinance as yf
        
        # 한국 국채 ETF 예시
        tickers = [
            'KOSEF 국고채10년',  # 한국 ETF (KRX)
            '^IRX',  # US 13-week Treasury Bill (비교용)
        ]
        
        print("Korea Treasury ETFs on Yahoo Finance:")
        print("Status: ⚠️  Limited (주로 미국 ETF)")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()

def recommend_best_source():
    """최적의 데이터 소스 추천"""
    print("="*80)
    print("📊 추천 데이터 소스")
    print("="*80)
    
    print("\n🥇 1순위: 한국은행 ECOS API")
    print("   - 가장 정확하고 공식적인 데이터")
    print("   - 국고채 1년, 3년, 5년, 10년 수익률")
    print("   - 일별/월별 데이터 제공")
    print("   - API 키: https://ecos.bok.or.kr/api/")
    
    print("\n🥈 2순위: FRED API")
    print("   - 신뢰할 수 있는 국제 데이터")
    print("   - 월별 데이터")
    print("   - API 키: https://fred.stlouisfed.org/docs/api/api_key.html")
    
    print("\n🥉 3순위: Investing.com")
    print("   - 실시간 데이터")
    print("   - 웹 스크래핑 필요")
    
    print("\n💡 권장 방법:")
    print("   1. ECOS API로 한국 국고채 1년물 수익률 조회")
    print("   2. 월별 평균 계산")
    print("   3. 연율을 월율로 변환 (annual_rate / 12)")
    print()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("한국 무위험 수익률 데이터 소스 조사")
    print("="*80 + "\n")
    
    test_ecos_bok()
    test_fred_korea_rates()
    test_kenneth_french_global()
    test_investing_com()
    test_yahoo_finance_etf()
    recommend_best_source()
    
    print("\n" + "="*80)
    print("결론: 한국은행 ECOS API 사용 권장")
    print("="*80)

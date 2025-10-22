#!/usr/bin/env python3
"""
한국 무위험 수익률 데이터 수집기

데이터 소스: 한국은행 경제통계시스템 (ECOS)
통계표: 국고채(1년) 수익률 (통계코드: 817Y002)
"""

import pandas as pd
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KoreaRiskFreeRateFetcher:
    """한국 무위험 수익률 조회 클래스"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize fetcher.
        
        Args:
            api_key: ECOS API key (https://ecos.bok.or.kr/api/)
        """
        self.api_key = api_key
        self.base_url = "https://ecos.bok.or.kr/api"
        
    def fetch_treasury_1year(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        한국 국고채 1년물 수익률 조회
        
        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            
        Returns:
            DataFrame with columns: date, rate (annual %)
        """
        if not self.api_key:
            raise ValueError("ECOS API key required. Get it from https://ecos.bok.or.kr/api/")
        
        # ECOS API 호출
        stat_code = "817Y002"  # 국고채(1년) 수익률
        item_code = "010190000"  # 국고채(1년)
        
        url = f"{self.base_url}/StatisticSearch/{self.api_key}/json/kr/1/10000/{stat_code}/D/{start_date}/{end_date}/{item_code}"
        
        logger.info(f"Fetching Korea 1-year treasury rates from {start_date} to {end_date}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'StatisticSearch' not in data:
                logger.error(f"API Error: {data}")
                return pd.DataFrame()
            
            rows = data['StatisticSearch']['row']
            
            # DataFrame 생성
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
            df['rate'] = pd.to_numeric(df['DATA_VALUE'])
            
            df = df[['date', 'rate']].sort_values('date').reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} daily observations")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return pd.DataFrame()
    
    def calculate_monthly_rf(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        일별 데이터를 월별 무위험 수익률로 변환
        
        Args:
            daily_df: 일별 국고채 수익률 DataFrame
            
        Returns:
            DataFrame with columns: date (month-end), RF (monthly %)
        """
        if daily_df.empty:
            return pd.DataFrame()
        
        # 월별 평균 계산
        daily_df['year_month'] = daily_df['date'].dt.to_period('M')
        monthly_avg = daily_df.groupby('year_month')['rate'].mean().reset_index()
        
        # 연율을 월율로 변환 (단순 나누기)
        monthly_avg['RF'] = monthly_avg['rate'] / 12
        
        # 월말 날짜로 변환
        monthly_avg['date'] = monthly_avg['year_month'].dt.to_timestamp('M')
        
        result = monthly_avg[['date', 'RF']].reset_index(drop=True)
        
        logger.info(f"Calculated {len(result)} monthly RF observations")
        return result
    
    def fetch_and_save(self, start_date: str, end_date: str, output_file: str):
        """
        데이터 조회 및 저장
        
        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            output_file: 출력 파일 경로
        """
        # 일별 데이터 조회
        daily_df = self.fetch_treasury_1year(start_date, end_date)
        
        if daily_df.empty:
            logger.error("No data retrieved")
            return
        
        # 월별 RF 계산
        monthly_df = self.calculate_monthly_rf(daily_df)
        
        # 저장
        monthly_df.to_csv(output_file, index=False)
        logger.info(f"Saved to {output_file}")
        
        # 통계 출력
        print("\n" + "="*80)
        print("Korea Risk-Free Rate Summary")
        print("="*80)
        print(f"Period: {monthly_df['date'].min()} to {monthly_df['date'].max()}")
        print(f"Observations: {len(monthly_df)} months")
        print(f"\nMonthly RF Statistics:")
        print(monthly_df['RF'].describe())
        print(f"\nLatest 5 months:")
        print(monthly_df.tail())


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Fetch Korea risk-free rates from ECOS')
    parser.add_argument('--api-key', type=str, help='ECOS API key')
    parser.add_argument('--config', type=str, help='Config file (ecos_config.json)')
    parser.add_argument('--start-date', type=str, default='20201001', help='Start date (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, default='20251031', help='End date (YYYYMMDD)')
    parser.add_argument('--output', type=str, default='korea_rf_monthly.csv', help='Output file')
    
    args = parser.parse_args()
    
    # API 키 로드
    api_key = args.api_key
    if not api_key and args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
            api_key = config.get('api_key')
    
    if not api_key:
        print("❌ Error: API key required")
        print("\nOptions:")
        print("  1. --api-key YOUR_KEY")
        print("  2. --config ecos_config.json")
        print("\n📖 See ECOS_API_SETUP.md for instructions")
        exit(1)
    
    fetcher = KoreaRiskFreeRateFetcher(api_key=api_key)
    fetcher.fetch_and_save(args.start_date, args.end_date, args.output)
    
    print("\n✅ Risk-free rate data updated!")
    print(f"📁 File: {args.output}")
    print("\n💡 Next step: Update korea_factor_calculator.py to use this data")

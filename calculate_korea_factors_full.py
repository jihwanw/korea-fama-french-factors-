#!/usr/bin/env python3
"""
Calculate Korea Fama-French factors for the entire period (2020-10 to 2025-10)
"""

import wrds
from korea_factor_calculator import KoreaFactorCalculator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("한국 시장 Fama-French 팩터 계산 (2020-10 ~ 2025-10)")
    logger.info("="*80)
    
    # Connect to WRDS
    logger.info("WRDS 연결 중...")
    conn = wrds.Connection()
    
    # Initialize calculator
    calculator = KoreaFactorCalculator(conn, risk_free_rate=0.01/12)
    
    # Calculate factors for entire period
    logger.info("\n팩터 계산 시작...")
    logger.info("예상 소요 시간: 10-15분")
    logger.info("총 60개월 계산 예정\n")
    
    factors_df = calculator.calculate_factors_for_period('2020-10-01', '2025-10-31')
    
    # Save results
    output_file = 'data/korea_factors_monthly.csv'
    calculator.save_factors(factors_df, output_file)
    
    # Display summary
    logger.info("\n" + "="*80)
    logger.info("계산 완료!")
    logger.info("="*80)
    logger.info(f"총 {len(factors_df)}개월 팩터 계산 완료")
    logger.info(f"저장 위치: {output_file}")
    
    logger.info("\n팩터 통계:")
    logger.info(factors_df[['MKT', 'SMB', 'HML']].describe())
    
    logger.info("\n최근 6개월 팩터:")
    logger.info(factors_df.tail(6))
    
    conn.close()
    logger.info("\n✅ 모든 작업 완료!")

if __name__ == "__main__":
    main()

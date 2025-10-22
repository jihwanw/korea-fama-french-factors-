#!/usr/bin/env python3
"""
Korea Market Fama-MacBeth Analysis

Analyzes Size Premium in Korean stock market using Korea-specific Fama-French factors.
"""

import pandas as pd
import numpy as np
import wrds
import statsmodels.api as sm
from scipy import stats as scipy_stats
from tqdm import tqdm
import logging
from korea_ticker_utils import get_korea_top_n_stocks, get_korea_stock_prices
from korea_factor_calculator import KoreaFactorCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_korea_fama_macbeth(start_date='2020-10-15', end_date='2025-10-17', n_stocks=200):
    """
    Run Fama-MacBeth regression for Korean market.
    
    Args:
        start_date: Start date for analysis
        end_date: End date for analysis
        n_stocks: Number of top stocks to analyze (default: 200)
    """
    logger.info("="*80)
    logger.info(f"한국 시장 Fama-MacBeth 분석 (상위 {n_stocks}개 종목)")
    logger.info("="*80)
    
    # Connect to WRDS
    logger.info("\nWRDS 연결 중...")
    conn = wrds.Connection()
    
    # 1. Get top N Korean stocks
    logger.info(f"\n{start_date} 기준 시가총액 상위 {n_stocks}개 종목 조회...")
    top_stocks = get_korea_top_n_stocks(n_stocks, start_date, conn)
    logger.info(f"✓ {len(top_stocks)}개 종목 조회 완료")
    
    # 2. Get stock prices first (needed for trading dates)
    logger.info(f"\n주식 가격 데이터 수집 중 ({start_date} ~ {end_date})...")
    gvkeys = top_stocks['gvkey'].tolist()
    prices_df = get_korea_stock_prices(gvkeys, start_date, end_date, conn)
    
    # 3. Load Korea factors
    logger.info("\n한국 팩터 로드 중...")
    factors_df = pd.read_csv('data/korea_factors_monthly.csv', parse_dates=['date'])
    logger.info(f"✓ {len(factors_df)}개월 팩터 로드 완료")
    
    # Convert monthly factors to daily by forward-filling
    logger.info("\n월별 팩터를 일별로 변환 중...")
    
    # Get all trading dates from stock data
    all_trading_dates = sorted(set(pd.to_datetime(prices_df['datadate'])))
    logger.info(f"거래일 수: {len(all_trading_dates)}")
    
    # Create daily factors by assigning monthly values to all days in that month
    daily_factors_list = []
    for date in all_trading_dates:
        # Find matching month in factors
        matching_factor = factors_df[
            (pd.to_datetime(factors_df['date']).dt.year == date.year) &
            (pd.to_datetime(factors_df['date']).dt.month == date.month)
        ]
        
        if len(matching_factor) > 0:
            factor_row = matching_factor.iloc[0]
            daily_factors_list.append({
                'date': date,
                'Mkt-RF': factor_row['MKT'] / 100 / 21,  # Monthly to daily approx
                'SMB': factor_row['SMB'] / 100 / 21,
                'HML': factor_row['HML'] / 100 / 21,
                'RF': factor_row['RF'] / 100 / 21
            })
    
    ff_factors = pd.DataFrame(daily_factors_list).set_index('date')
    logger.info(f"✓ {len(ff_factors)}일 팩터 생성 완료")
    
    # 4. Calculate daily returns for each stock
    logger.info("\n일별 수익률 계산 중...")
    stock_returns = {}
    for gvkey in tqdm(gvkeys, desc="수익률 계산"):
        stock_data = prices_df[prices_df['gvkey'] == gvkey].copy()
        if len(stock_data) < 100:  # Skip stocks with insufficient data
            continue
        
        stock_data = stock_data.sort_values('datadate')
        stock_data['returns'] = stock_data['prccd'].pct_change()
        stock_data = stock_data.set_index('datadate')
        stock_returns[gvkey] = stock_data['returns']
    
    logger.info(f"✓ {len(stock_returns)}개 종목 수익률 계산 완료")
    
    conn.close()
    
    # Stage 1: Time-series regression (estimate betas)
    logger.info("\n" + "="*80)
    logger.info("1단계: 시계열 회귀 (Time-Series Regression)")
    logger.info("각 주식의 팩터 노출도(베타) 추정")
    logger.info("="*80)
    
    betas = {}
    for gvkey in tqdm(stock_returns.keys(), desc="베타 추정"):
        stock_ret = stock_returns[gvkey]
        
        # Ensure both have datetime index
        stock_ret.index = pd.to_datetime(stock_ret.index)
        
        # Align dates
        common_dates = stock_ret.index.intersection(ff_factors.index)
        
        if len(common_dates) < 100:
            logger.debug(f"Skipping {gvkey}: only {len(common_dates)} common dates")
            continue
        
        y = stock_ret.loc[common_dates] - ff_factors.loc[common_dates, 'RF']
        X = ff_factors.loc[common_dates, ['Mkt-RF', 'SMB', 'HML']]
        X = sm.add_constant(X)
        
        try:
            model = sm.OLS(y, X, missing='drop').fit()
            betas[gvkey] = {
                'alpha': model.params['const'],
                'beta_market': model.params['Mkt-RF'],
                'beta_smb': model.params['SMB'],
                'beta_hml': model.params['HML'],
                'r_squared': model.rsquared
            }
        except Exception as e:
            logger.debug(f"Failed to estimate beta for {gvkey}: {e}")
            continue
    
    logger.info(f"\n✓ {len(betas)}개 주식의 베타 추정 완료")
    
    # Beta summary statistics
    betas_df = pd.DataFrame(betas).T
    logger.info(f"\n베타 요약 통계:")
    logger.info(betas_df[['beta_market', 'beta_smb', 'beta_hml']].describe())
    
    # Stage 2: Cross-sectional regression
    logger.info("\n" + "="*80)
    logger.info("2단계: 횡단면 회귀 (Cross-Sectional Regression)")
    logger.info("각 시점에서 팩터 프리미엄 추정")
    logger.info("="*80)
    
    common_dates = ff_factors.index
    gammas = []
    
    logger.info(f"\n{len(common_dates)}개 시점에 대해 횡단면 회귀 실행 중...")
    
    for date in tqdm(common_dates, desc="횡단면 회귀"):
        returns_t = []
        betas_t = []
        
        for gvkey in betas.keys():
            if gvkey in stock_returns:
                if date in stock_returns[gvkey].index:
                    ret = stock_returns[gvkey].loc[date] - ff_factors.loc[date, 'RF']
                    returns_t.append(ret)
                    betas_t.append([
                        betas[gvkey]['beta_market'],
                        betas[gvkey]['beta_smb'],
                        betas[gvkey]['beta_hml']
                    ])
        
        if len(returns_t) < 10:
            continue
        
        # Cross-sectional regression
        y = np.array(returns_t)
        X = np.array(betas_t)
        X = sm.add_constant(X)
        
        try:
            model = sm.OLS(y, X).fit()
            gammas.append({
                'date': date,
                'gamma_0': model.params[0],
                'gamma_market': model.params[1],
                'gamma_smb': model.params[2],
                'gamma_hml': model.params[3]
            })
        except:
            continue
    
    logger.info(f"\n✓ {len(gammas)}개 시점의 횡단면 회귀 완료")
    
    # Stage 3: Time-series average and t-test
    gammas_df = pd.DataFrame(gammas)
    
    logger.info("\n" + "="*80)
    logger.info("한국 시장 Fama-MacBeth 검정 결과")
    logger.info("="*80)
    logger.info(f"\n분석 기간: {start_date} ~ {end_date}")
    logger.info(f"횡단면 회귀 횟수: {len(gammas)}일")
    logger.info(f"평균 주식 수: {len(betas)}개")
    
    logger.info("\n" + "="*80)
    logger.info("팩터 프리미엄 추정 결과")
    logger.info("="*80)
    logger.info(f"\n{'팩터':<20s} {'일별 프리미엄':>12s} {'연간 프리미엄':>12s} {'t-통계량':>10s} {'p-value':>10s} {'유의성':>8s}")
    logger.info("-"*80)
    
    results = []
    
    for factor, col in [('Market (Mkt-RF)', 'gamma_market'), 
                        ('Size (SMB)', 'gamma_smb'), 
                        ('Value (HML)', 'gamma_hml')]:
        mean_gamma = gammas_df[col].mean()
        std_gamma = gammas_df[col].std()
        t_stat = mean_gamma / (std_gamma / np.sqrt(len(gammas_df)))
        p_value = 2 * (1 - scipy_stats.t.cdf(abs(t_stat), len(gammas_df) - 1))
        
        # Annualize
        annual_premium = mean_gamma * 252
        
        # Significance
        if p_value < 0.01:
            sig = '***'
        elif p_value < 0.05:
            sig = '**'
        elif p_value < 0.1:
            sig = '*'
        else:
            sig = ''
        
        results.append({
            'factor': factor,
            'daily': mean_gamma,
            'annual': annual_premium,
            't_stat': t_stat,
            'p_value': p_value,
            'sig': sig
        })
        
        logger.info(f"{factor:<20s} {mean_gamma:>11.4%} {annual_premium:>11.2%} {t_stat:>10.2f} {p_value:>10.4f} {sig:>8s}")
    
    logger.info(f"\n주: *** p<0.01, ** p<0.05, * p<0.1")
    
    # Interpretation
    logger.info("\n" + "="*80)
    logger.info("결과 해석")
    logger.info("="*80)
    
    for r in results:
        logger.info(f"\n{r['factor']}:")
        logger.info(f"  - 일별 프리미엄: {r['daily']:.4%}")
        logger.info(f"  - 연간 프리미엄: {r['annual']:.2%}")
        logger.info(f"  - t-통계량: {r['t_stat']:.2f}")
        
        if r['p_value'] < 0.01:
            logger.info(f"  - 결론: 매우 유의함 (p < 0.01) ✓✓✓")
            logger.info(f"  - 해석: 이 팩터는 수익률을 강하게 설명합니다.")
        elif r['p_value'] < 0.05:
            logger.info(f"  - 결론: 유의함 (p < 0.05) ✓✓")
            logger.info(f"  - 해석: 이 팩터는 수익률을 설명합니다.")
        elif r['p_value'] < 0.1:
            logger.info(f"  - 결론: 약하게 유의함 (p < 0.1) ✓")
            logger.info(f"  - 해석: 이 팩터는 약하게 수익률을 설명합니다.")
        else:
            logger.info(f"  - 결론: 유의하지 않음 (p > 0.1) ✗")
            logger.info(f"  - 해석: 이 팩터는 수익률을 설명하지 못합니다.")
    
    # Save results
    logger.info("\n결과 저장 중...")
    betas_df.to_csv('results/korea/korea_stage1_betas.csv')
    logger.info("✓ 1단계 결과 저장: results/korea/korea_stage1_betas.csv")
    
    gammas_df.to_csv('results/korea/korea_stage2_cross_sectional.csv')
    logger.info("✓ 2단계 결과 저장: results/korea/korea_stage2_cross_sectional.csv")
    
    # Save summary
    with open('results/korea/korea_fama_macbeth_output.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("한국 시장 Fama-MacBeth 분석 결과\n")
        f.write("="*80 + "\n\n")
        f.write(f"분석 기간: {start_date} ~ {end_date}\n")
        f.write(f"분석 주식 수: {len(betas)}개\n")
        f.write(f"횡단면 회귀 횟수: {len(gammas)}일\n\n")
        f.write("="*80 + "\n")
        f.write("팩터 프리미엄 추정 결과\n")
        f.write("="*80 + "\n\n")
        f.write(f"{'팩터':<20s} {'연간 프리미엄':>15s} {'t-통계량':>12s} {'p-value':>12s} {'유의성':>10s}\n")
        f.write("-"*80 + "\n")
        
        for r in results:
            f.write(f"{r['factor']:<20s} {r['annual']:>14.2%} {r['t_stat']:>12.2f} {r['p_value']:>12.4f} {r['sig']:>10s}\n")
        
        f.write("\n주: *** p<0.01, ** p<0.05, * p<0.1\n")
    
    logger.info("✓ 요약 저장: results/korea/korea_fama_macbeth_output.txt")
    
    logger.info("\n" + "="*80)
    logger.info("✅ 한국 시장 Fama-MacBeth 분석 완료!")
    logger.info("="*80)
    
    return results, betas_df, gammas_df


if __name__ == "__main__":
    # Run with 300 stocks
    results, betas_df, gammas_df = run_korea_fama_macbeth(n_stocks=300)

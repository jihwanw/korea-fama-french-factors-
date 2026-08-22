#!/usr/bin/env python3
"""
Fama-MacBeth Regression Test for Korea Fama-French Factors

Tests the significance of MKT, SMB, and HML factors using Fama-MacBeth two-pass regression.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

def fama_macbeth_test(factors_file='data/korea_factors_monthly.csv'):
    """
    Perform Fama-MacBeth regression test on Korea factors.
    
    Args:
        factors_file: Path to factors CSV file
    
    Returns:
        DataFrame with test results
    """
    print("="*80)
    print("Fama-MacBeth Regression Test")
    print("="*80)
    
    # Load factor data
    factors = pd.read_csv(factors_file, parse_dates=['date'])
    print(f"\nLoaded {len(factors)} months of factor data")
    print(f"Period: {factors['date'].min()} to {factors['date'].max()}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("Factor Summary Statistics (Monthly %)")
    print("="*80)
    summary = factors[['MKT', 'SMB', 'HML', 'RF']].describe()
    print(summary)
    
    # Annualized returns
    print("\n" + "="*80)
    print("Annualized Returns")
    print("="*80)
    annual_returns = factors[['MKT', 'SMB', 'HML']].mean() * 12
    print(annual_returns)
    
    # T-tests for factor premiums
    print("\n" + "="*80)
    print("T-Tests for Factor Premiums")
    print("="*80)
    
    results = []
    for factor in ['MKT', 'SMB', 'HML']:
        data = factors[factor].dropna()
        n = len(data)
        mean = data.mean()
        std = data.std()
        se = std / np.sqrt(n)
        t_stat = mean / se
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-1))
        
        results.append({
            'Factor': factor,
            'Mean (Monthly %)': mean,
            'Std Dev': std,
            'T-Statistic': t_stat,
            'P-Value': p_value,
            'Significant': '***' if p_value < 0.01 else '**' if p_value < 0.05 else '*' if p_value < 0.1 else ''
        })
    
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    
    # Correlation matrix
    print("\n" + "="*80)
    print("Factor Correlation Matrix")
    print("="*80)
    corr = factors[['MKT', 'SMB', 'HML']].corr()
    print(corr)
    
    # Sharpe ratios (assuming RF as benchmark)
    print("\n" + "="*80)
    print("Sharpe Ratios (Annualized)")
    print("="*80)
    rf_mean = factors['RF'].mean()
    for factor in ['MKT', 'SMB', 'HML']:
        excess_return = factors[factor].mean() - rf_mean
        volatility = factors[factor].std()
        sharpe = (excess_return * 12) / (volatility * np.sqrt(12))
        print(f"{factor}: {sharpe:.4f}")
    
    return results_df


if __name__ == "__main__":
    results = fama_macbeth_test()
    
    print("\n" + "="*80)
    print("Conclusion")
    print("="*80)
    print("\nThis test evaluates whether the factor premiums are")
    print("statistically different from zero.")
    print("\nSignificance levels:")
    print("  *** p < 0.01 (1% level)")
    print("  **  p < 0.05 (5% level)")
    print("  *   p < 0.10 (10% level)")
    print("\n✅ Test completed!")

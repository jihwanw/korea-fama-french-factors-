#!/usr/bin/env python3
"""
Korea Fama-French Factor Calculator

This module calculates Korea-specific Fama-French three factors (MKT, SMB, HML)
following the methodology of Fama and French (1993).
"""

import pandas as pd
import numpy as np
import wrds
from typing import Dict, List, Tuple
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from korea_ticker_utils import get_korea_all_stocks, get_korea_stock_prices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KoreaFactorCalculator:
    """
    Calculate Fama-French factors for Korean market.
    
    Methodology:
    - Size: Median market cap split (Small vs Big)
    - Value: 30th and 70th percentile B/M split (Value, Neutral, Growth)
    - 6 portfolios: S/L, S/M, S/H, B/L, B/M, B/H
    - SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
    - HML = (S/L + B/L)/2 - (S/H + B/H)/2
    - MKT = Value-weighted market return - RF
    """
    
    def __init__(self, conn: wrds.Connection, risk_free_rate: float = 0.01/12):
        """
        Initialize calculator.
        
        Args:
            conn: WRDS connection object
            risk_free_rate: Monthly risk-free rate (default: 1% annual / 12)
        """
        self.conn = conn
        self.risk_free_rate = risk_free_rate
        logger.info(f"Initialized KoreaFactorCalculator with RF={risk_free_rate*12*100:.2f}% annual")
    
    def find_previous_trading_day(self, target_date: str, max_days_back: int = 10) -> str:
        """
        Find the most recent trading day with data before or on target_date.
        
        Args:
            target_date: Target date in 'YYYY-MM-DD' format
            max_days_back: Maximum days to search backwards
        
        Returns:
            Date string of previous trading day with data
        """
        query = f"""
        SELECT DISTINCT datadate
        FROM comp.g_secd
        WHERE fic = 'KOR'
        AND datadate <= '{target_date}'
        AND datadate >= DATE '{target_date}' - INTERVAL '{max_days_back}' DAY
        AND prccd IS NOT NULL
        ORDER BY datadate DESC
        LIMIT 1
        """
        
        result = self.conn.raw_sql(query)
        if len(result) > 0:
            trading_day = str(result['datadate'].iloc[0])[:10]
            logger.info(f"Found trading day: {trading_day} for target: {target_date}")
            return trading_day
        else:
            logger.warning(f"No trading day found near {target_date}")
            return target_date
    
    def form_portfolios(self, stocks_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Form 6 portfolios based on size and value (2x3 sort).
        
        Args:
            stocks_df: DataFrame with gvkey, market_cap, book_to_market
        
        Returns:
            Dictionary with portfolio names as keys, list of gvkeys as values
        """
        # Size breakpoint: median
        size_median = stocks_df['market_cap'].median()
        
        # Value breakpoints: 30th and 70th percentile
        bm_30 = stocks_df['book_to_market'].quantile(0.30)
        bm_70 = stocks_df['book_to_market'].quantile(0.70)
        
        logger.info(f"Size median: {size_median/1e12:.2f}T KRW")
        logger.info(f"B/M 30th percentile: {bm_30:.6f}")
        logger.info(f"B/M 70th percentile: {bm_70:.6f}")
        
        # Assign stocks to portfolios
        portfolios = {
            'S/L': [],  # Small Value
            'S/M': [],  # Small Neutral
            'S/H': [],  # Small Growth
            'B/L': [],  # Big Value
            'B/M': [],  # Big Neutral
            'B/H': []   # Big Growth
        }
        
        for _, stock in stocks_df.iterrows():
            gvkey = stock['gvkey']
            mc = stock['market_cap']
            bm = stock['book_to_market']
            
            # Determine size category
            size_cat = 'S' if mc <= size_median else 'B'
            
            # Determine value category
            if bm <= bm_30:
                value_cat = 'H'  # Growth (High B/M is actually low, confusing naming)
            elif bm >= bm_70:
                value_cat = 'L'  # Value (Low B/M is actually high)
            else:
                value_cat = 'M'  # Neutral
            
            portfolio_name = f"{size_cat}/{value_cat}"
            portfolios[portfolio_name].append(gvkey)
        
        # Log portfolio sizes
        for name, stocks in portfolios.items():
            logger.info(f"Portfolio {name}: {len(stocks)} stocks")
        
        return portfolios
    
    def calculate_portfolio_return(self, portfolio_gvkeys: List[str], 
                                   returns_df: pd.DataFrame) -> float:
        """
        Calculate value-weighted return for a portfolio.
        
        Args:
            portfolio_gvkeys: List of gvkeys in the portfolio
            returns_df: DataFrame with gvkey, monthly_return, market_cap
        
        Returns:
            Portfolio return (float)
        """
        # Filter to portfolio stocks
        portfolio_data = returns_df[returns_df['gvkey'].isin(portfolio_gvkeys)].copy()
        
        if len(portfolio_data) == 0:
            logger.warning("Empty portfolio, returning 0")
            return 0.0
        
        # Remove stocks with missing returns
        portfolio_data = portfolio_data[portfolio_data['monthly_return'].notna()]
        
        if len(portfolio_data) == 0:
            logger.warning("No valid returns in portfolio, returning 0")
            return 0.0
        
        # Calculate value-weighted return
        total_market_cap = portfolio_data['market_cap'].sum()
        if total_market_cap == 0:
            return 0.0
        
        weighted_return = (portfolio_data['monthly_return'] * portfolio_data['market_cap']).sum() / total_market_cap
        
        return weighted_return
    
    def calculate_monthly_factors(self, year: int, month: int) -> Dict[str, float]:
        """
        Calculate factors for a specific month.
        
        Args:
            year: Year (e.g., 2020)
            month: Month (1-12)
        
        Returns:
            Dictionary with 'date', 'MKT', 'SMB', 'HML', 'RF'
        """
        logger.info(f"Calculating factors for {year}-{month:02d}")
        
        # Get portfolio formation date (end of previous month)
        current_date = datetime(year, month, 1)
        formation_date_target = (current_date - relativedelta(months=1)).strftime('%Y-%m-%d')
        formation_date = self.find_previous_trading_day(formation_date_target)
        
        # Get month-end date for returns
        if month == 12:
            end_date = datetime(year, 12, 31).strftime('%Y-%m-%d')
        else:
            end_date = (datetime(year, month+1, 1) - relativedelta(days=1)).strftime('%Y-%m-%d')
        
        start_date = datetime(year, month, 1).strftime('%Y-%m-%d')
        
        logger.info(f"Formation date: {formation_date}, Return period: {start_date} to {end_date}")
        
        # Get all stocks with market cap and book-to-market
        try:
            stocks_df = get_korea_all_stocks(formation_date, self.conn)
        except Exception as e:
            logger.error(f"Failed to get stocks for {formation_date}: {e}")
            return None
        
        if len(stocks_df) < 100:
            logger.warning(f"Only {len(stocks_df)} stocks available, skipping")
            return None
        
        # Form portfolios
        portfolios = self.form_portfolios(stocks_df)
        
        # Get returns for the month (need previous month for return calculation)
        all_gvkeys = stocks_df['gvkey'].tolist()
        prev_month_start = (datetime(year, month, 1) - relativedelta(months=1)).strftime('%Y-%m-%d')
        
        try:
            prices_df = get_korea_stock_prices(all_gvkeys, prev_month_start, end_date, self.conn)
        except Exception as e:
            logger.error(f"Failed to get prices: {e}")
            return None
        
        # Get month-end prices
        prices_df['month'] = pd.to_datetime(prices_df['datadate']).dt.to_period('M')
        monthly_df = prices_df.sort_values(['gvkey', 'iid', 'datadate'])
        monthly_df = monthly_df.groupby(['gvkey', 'iid', 'month']).last().reset_index()
        
        # Calculate monthly returns
        monthly_df = monthly_df.sort_values(['gvkey', 'iid', 'month'])
        monthly_df['monthly_return'] = monthly_df.groupby(['gvkey', 'iid'])['prccd'].pct_change()
        
        # Filter to current month only
        current_month = pd.Period(f"{year}-{month:02d}", freq='M')
        monthly_df = monthly_df[monthly_df['month'] == current_month]
        
        # Remove stocks without valid returns
        monthly_df = monthly_df[monthly_df['monthly_return'].notna()]
        
        # Calculate portfolio returns
        portfolio_returns = {}
        for name, gvkeys in portfolios.items():
            ret = self.calculate_portfolio_return(gvkeys, monthly_df)
            portfolio_returns[name] = ret
            logger.info(f"Portfolio {name} return: {ret*100:.2f}%")
        
        # Calculate factors
        # SMB = (S/L + S/M + S/H)/3 - (B/L + B/M + B/H)/3
        smb = (portfolio_returns['S/L'] + portfolio_returns['S/M'] + portfolio_returns['S/H']) / 3 - \
              (portfolio_returns['B/L'] + portfolio_returns['B/M'] + portfolio_returns['B/H']) / 3
        
        # HML = (S/L + B/L)/2 - (S/H + B/H)/2
        hml = (portfolio_returns['S/L'] + portfolio_returns['B/L']) / 2 - \
              (portfolio_returns['S/H'] + portfolio_returns['B/H']) / 2
        
        # MKT = Value-weighted market return - RF
        total_market_cap = monthly_df['market_cap'].sum()
        if total_market_cap > 0:
            market_return = (monthly_df['monthly_return'] * monthly_df['market_cap']).sum() / total_market_cap
        else:
            market_return = 0.0
        
        mkt = market_return - self.risk_free_rate
        
        logger.info(f"MKT: {mkt*100:.2f}%, SMB: {smb*100:.2f}%, HML: {hml*100:.2f}%")
        
        return {
            'date': end_date,
            'MKT': mkt * 100,  # Convert to percentage
            'SMB': smb * 100,
            'HML': hml * 100,
            'RF': self.risk_free_rate * 100
        }
    
    def calculate_factors_for_period(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Calculate factors for entire period.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        
        Returns:
            DataFrame with date, MKT, SMB, HML, RF
        """
        logger.info(f"Calculating factors from {start_date} to {end_date}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        factors_list = []
        current = start
        
        while current <= end:
            year = current.year
            month = current.month
            
            factors = self.calculate_monthly_factors(year, month)
            
            if factors is not None:
                factors_list.append(factors)
            
            # Move to next month
            current = current + relativedelta(months=1)
        
        df = pd.DataFrame(factors_list)
        logger.info(f"Calculated factors for {len(df)} months")
        
        return df
    
    def save_factors(self, factors_df: pd.DataFrame, filepath: str):
        """Save factors to CSV file."""
        factors_df.to_csv(filepath, index=False)
        logger.info(f"Saved factors to {filepath}")
    
    def load_factors(self, filepath: str) -> pd.DataFrame:
        """Load factors from CSV file."""
        df = pd.read_csv(filepath, parse_dates=['date'])
        logger.info(f"Loaded {len(df)} months of factors from {filepath}")
        return df


if __name__ == "__main__":
    # Test the calculator
    import wrds
    
    conn = wrds.Connection()
    calculator = KoreaFactorCalculator(conn)
    
    # Test: Calculate factors for Oct-Dec 2020
    print("="*80)
    print("Testing Korea Factor Calculator")
    print("="*80)
    
    factors = calculator.calculate_factors_for_period('2020-10-01', '2020-12-31')
    print("\nCalculated factors:")
    print(factors)
    
    # Save test results
    calculator.save_factors(factors, 'data/korea_factors_test.csv')
    
    conn.close()
    print("\n✅ Test completed!")

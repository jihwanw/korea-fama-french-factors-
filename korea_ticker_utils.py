#!/usr/bin/env python3
"""
Korea Stock Data Utilities

This module provides functions to retrieve Korean stock data from WRDS Compustat Global.
"""

import pandas as pd
import wrds
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_korea_top_n_stocks(n: int, date: str, conn: wrds.Connection) -> pd.DataFrame:
    """
    Get top N Korean stocks by market capitalization on a specific date.
    
    Args:
        n: Number of stocks to retrieve
        date: Reference date in 'YYYY-MM-DD' format
        conn: WRDS connection object
    
    Returns:
        DataFrame with columns: gvkey, iid, conm, prccd, market_cap
        Sorted by market_cap descending
    
    Example:
        >>> conn = wrds.Connection()
        >>> top100 = get_korea_top_n_stocks(100, '2020-10-15', conn)
        >>> print(top100.head())
    """
    logger.info(f"Retrieving top {n} Korean stocks as of {date}")
    
    query = f"""
    SELECT gvkey, iid, conm,
           prccd, ajexdi, cshoc,
           (prccd / ajexdi * cshoc) as market_cap
    FROM comp.g_secd
    WHERE fic = 'KOR'
    AND datadate = '{date}'
    AND prccd IS NOT NULL
    AND cshoc IS NOT NULL
    AND cshoc > 0
    ORDER BY market_cap DESC
    LIMIT {n}
    """
    
    try:
        df = conn.raw_sql(query)
        logger.info(f"Successfully retrieved {len(df)} stocks")
        
        if len(df) < n:
            logger.warning(f"Only {len(df)} stocks found, requested {n}")
        
        return df
    
    except Exception as e:
        logger.error(f"Failed to retrieve Korean stocks: {e}")
        raise


def get_korea_stock_prices(gvkeys: List[str], start_date: str, end_date: str, 
                           conn: wrds.Connection) -> pd.DataFrame:
    """
    Get daily prices for Korean stocks.
    
    Args:
        gvkeys: List of gvkey identifiers
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        conn: WRDS connection object
    
    Returns:
        DataFrame with columns: gvkey, iid, datadate, prccd, returns
        
    Example:
        >>> prices = get_korea_stock_prices(['104604', '204049'], '2020-10-01', '2020-10-31', conn)
    """
    logger.info(f"Retrieving prices for {len(gvkeys)} stocks from {start_date} to {end_date}")
    
    # Create gvkey list for SQL IN clause
    gvkey_list = "','".join(gvkeys)
    
    query = f"""
    SELECT gvkey, iid, datadate, conm,
           prccd, ajexdi, cshoc,
           (prccd / ajexdi * cshoc) as market_cap
    FROM comp.g_secd
    WHERE gvkey IN ('{gvkey_list}')
    AND datadate BETWEEN '{start_date}' AND '{end_date}'
    AND prccd IS NOT NULL
    ORDER BY gvkey, iid, datadate
    """
    
    try:
        df = conn.raw_sql(query)
        logger.info(f"Retrieved {len(df)} price records")
        
        # Calculate returns
        df = df.sort_values(['gvkey', 'iid', 'datadate'])
        df['returns'] = df.groupby(['gvkey', 'iid'])['prccd'].pct_change()
        
        # Report missing data
        missing_pct = df['returns'].isna().sum() / len(df) * 100
        logger.info(f"Missing data: {missing_pct:.2f}%")
        
        return df
    
    except Exception as e:
        logger.error(f"Failed to retrieve stock prices: {e}")
        raise


def get_korea_all_stocks(date: str, conn: wrds.Connection, 
                         min_market_cap: float = 0) -> pd.DataFrame:
    """
    Get all Korean stocks with market cap and book value for factor calculation.
    
    Args:
        date: Reference date in 'YYYY-MM-DD' format
        conn: WRDS connection object
        min_market_cap: Minimum market cap filter (default: 0)
    
    Returns:
        DataFrame with columns: gvkey, iid, conm, market_cap, book_equity, book_to_market
        
    Example:
        >>> all_stocks = get_korea_all_stocks('2020-10-15', conn)
    """
    logger.info(f"Retrieving all Korean stocks as of {date}")
    
    # Get price and market cap data
    query_price = f"""
    SELECT gvkey, iid, conm, datadate,
           prccd, ajexdi, cshoc,
           (prccd / ajexdi * cshoc) as market_cap
    FROM comp.g_secd
    WHERE fic = 'KOR'
    AND datadate = '{date}'
    AND prccd IS NOT NULL
    AND cshoc IS NOT NULL
    AND cshoc > 0
    AND (prccd / ajexdi * cshoc) >= {min_market_cap}
    """
    
    try:
        df_price = conn.raw_sql(query_price)
        logger.info(f"Retrieved {len(df_price)} stocks with price data")
        
        # Get book equity from fundamentals (most recent annual data before the date)
        year = int(date[:4])
        query_fundamentals = f"""
        SELECT gvkey, datadate, ceq, at
        FROM comp.g_funda
        WHERE fic = 'KOR'
        AND datadate <= '{date}'
        AND datadate >= '{year-2}-01-01'
        AND ceq IS NOT NULL
        AND ceq > 0
        """
        
        df_fundamentals = conn.raw_sql(query_fundamentals)
        logger.info(f"Retrieved {len(df_fundamentals)} fundamental records")
        
        # Get most recent fundamental data for each gvkey
        df_fundamentals = df_fundamentals.sort_values('datadate', ascending=False)
        df_fundamentals = df_fundamentals.groupby('gvkey').first().reset_index()
        
        # Merge price and fundamental data
        df = df_price.merge(df_fundamentals[['gvkey', 'ceq', 'at']], 
                           on='gvkey', how='left', suffixes=('', '_fund'))
        
        # Calculate book-to-market ratio
        df['book_equity'] = df['ceq']
        df['book_to_market'] = df['book_equity'] / df['market_cap']
        
        # Remove stocks without book value
        df_with_bm = df[df['book_to_market'].notna()].copy()
        
        logger.info(f"Final dataset: {len(df_with_bm)} stocks with book-to-market data")
        logger.info(f"Dropped {len(df) - len(df_with_bm)} stocks without book value")
        
        return df_with_bm
    
    except Exception as e:
        logger.error(f"Failed to retrieve Korean stocks with fundamentals: {e}")
        raise


def get_korea_monthly_returns(gvkeys: List[str], start_date: str, end_date: str,
                              conn: wrds.Connection) -> pd.DataFrame:
    """
    Get monthly returns for Korean stocks.
    
    Args:
        gvkeys: List of gvkey identifiers
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        conn: WRDS connection object
    
    Returns:
        DataFrame with columns: gvkey, month, monthly_return, market_cap
        
    Example:
        >>> monthly_ret = get_korea_monthly_returns(['104604'], '2020-10-01', '2021-10-31', conn)
    """
    logger.info(f"Retrieving monthly returns for {len(gvkeys)} stocks")
    
    # Get daily prices
    df_daily = get_korea_stock_prices(gvkeys, start_date, end_date, conn)
    
    # Convert to monthly
    df_daily['month'] = pd.to_datetime(df_daily['datadate']).dt.to_period('M')
    
    # Get month-end prices and market caps
    df_monthly = df_daily.sort_values(['gvkey', 'iid', 'datadate'])
    df_monthly = df_monthly.groupby(['gvkey', 'iid', 'month']).last().reset_index()
    
    # Calculate monthly returns
    df_monthly = df_monthly.sort_values(['gvkey', 'iid', 'month'])
    df_monthly['monthly_return'] = df_monthly.groupby(['gvkey', 'iid'])['prccd'].pct_change()
    
    logger.info(f"Calculated monthly returns for {len(df_monthly)} month-stock observations")
    
    return df_monthly


if __name__ == "__main__":
    # Test the functions
    import wrds
    
    conn = wrds.Connection()
    
    # Test 1: Get top 10 stocks
    print("="*80)
    print("Test 1: Get top 10 Korean stocks (2020-10-15)")
    print("="*80)
    top10 = get_korea_top_n_stocks(10, '2020-10-15', conn)
    print(top10[['conm', 'market_cap']])
    
    # Test 2: Get prices for top 3 stocks
    print("\n" + "="*80)
    print("Test 2: Get prices for top 3 stocks (Oct 2020)")
    print("="*80)
    gvkeys = top10['gvkey'].head(3).tolist()
    prices = get_korea_stock_prices(gvkeys, '2020-10-01', '2020-10-31', conn)
    print(f"Retrieved {len(prices)} price records")
    print(prices.groupby('gvkey')['datadate'].count())
    
    # Test 3: Get all stocks with book-to-market
    print("\n" + "="*80)
    print("Test 3: Get all Korean stocks with book-to-market")
    print("="*80)
    all_stocks = get_korea_all_stocks('2020-10-15', conn)
    print(f"Total stocks: {len(all_stocks)}")
    print(f"Book-to-market stats:")
    print(all_stocks['book_to_market'].describe())
    
    conn.close()
    print("\n✅ All tests completed!")

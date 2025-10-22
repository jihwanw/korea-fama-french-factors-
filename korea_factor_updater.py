#!/usr/bin/env python3
"""
Korea Fama-French Factor Updater

This script updates the Korea factor data by calculating factors for new months.
It reads the existing data, identifies missing months, and calculates factors for them.
"""

import pandas as pd
import wrds
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from korea_factor_calculator import KoreaFactorCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_existing_factors(filepath: str = 'data/korea_factors_monthly.csv') -> pd.DataFrame:
    """Load existing factor data."""
    try:
        df = pd.read_csv(filepath, parse_dates=['date'])
        logger.info(f"Loaded {len(df)} existing factor observations")
        return df
    except FileNotFoundError:
        logger.warning(f"No existing data found at {filepath}")
        return pd.DataFrame(columns=['date', 'MKT', 'SMB', 'HML', 'RF'])


def get_missing_months(existing_df: pd.DataFrame, start_date: str, end_date: str) -> list:
    """
    Identify missing months between start_date and end_date.
    
    Args:
        existing_df: DataFrame with existing factor data
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        List of (year, month) tuples for missing months
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get all months in range
    all_months = []
    current = start
    while current <= end:
        all_months.append((current.year, current.month))
        current = current + relativedelta(months=1)
    
    # Get existing months
    if len(existing_df) > 0:
        existing_df['year_month'] = pd.to_datetime(existing_df['date']).dt.to_period('M')
        existing_months = set((ym.year, ym.month) for ym in existing_df['year_month'])
    else:
        existing_months = set()
    
    # Find missing months
    missing = [ym for ym in all_months if ym not in existing_months]
    
    logger.info(f"Found {len(missing)} missing months out of {len(all_months)} total months")
    
    return missing


def update_factors(filepath: str = 'data/korea_factors_monthly.csv',
                   start_date: str = '2020-10-01',
                   end_date: str = None):
    """
    Update factor data with missing months.
    
    Args:
        filepath: Path to factor data CSV file
        start_date: Start date for checking missing data
        end_date: End date for checking missing data (default: current month)
    """
    if end_date is None:
        # Default to last month (current month data not yet available)
        today = datetime.today()
        end_date = (today.replace(day=1) - relativedelta(days=1)).strftime('%Y-%m-%d')
    
    logger.info(f"Updating factors from {start_date} to {end_date}")
    
    # Load existing data
    existing_df = load_existing_factors(filepath)
    
    # Find missing months
    missing_months = get_missing_months(existing_df, start_date, end_date)
    
    if len(missing_months) == 0:
        logger.info("No missing months found. Data is up to date!")
        return existing_df
    
    logger.info(f"Missing months: {missing_months}")
    
    # Connect to WRDS
    logger.info("Connecting to WRDS...")
    conn = wrds.Connection()
    
    # Initialize calculator
    calculator = KoreaFactorCalculator(conn)
    
    # Calculate factors for missing months
    new_factors = []
    for year, month in missing_months:
        logger.info(f"Calculating factors for {year}-{month:02d}")
        try:
            factors = calculator.calculate_monthly_factors(year, month)
            if factors is not None:
                new_factors.append(factors)
        except Exception as e:
            logger.error(f"Failed to calculate factors for {year}-{month:02d}: {e}")
    
    conn.close()
    
    if len(new_factors) == 0:
        logger.warning("No new factors calculated")
        return existing_df
    
    # Combine with existing data
    new_df = pd.DataFrame(new_factors)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Sort by date
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    # Save updated data
    combined_df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(combined_df)} factor observations to {filepath}")
    logger.info(f"Added {len(new_factors)} new observations")
    
    return combined_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Korea Fama-French factors')
    parser.add_argument('--filepath', type=str, default='data/korea_factors_monthly.csv',
                       help='Path to factor data CSV file')
    parser.add_argument('--start-date', type=str, default='2020-10-01',
                       help='Start date for checking missing data (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date for checking missing data (YYYY-MM-DD, default: last month)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("Korea Fama-French Factor Updater")
    print("="*80)
    
    updated_df = update_factors(
        filepath=args.filepath,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    print("\n" + "="*80)
    print("Update Summary")
    print("="*80)
    print(f"Total observations: {len(updated_df)}")
    if len(updated_df) > 0:
        print(f"Date range: {updated_df['date'].min()} to {updated_df['date'].max()}")
        print("\nLatest 5 observations:")
        print(updated_df.tail())
    
    print("\n✅ Update completed!")

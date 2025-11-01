#!/usr/bin/env python3
"""
Script to check recent sentiment predictions
"""

import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from clickhouse_driver import Client
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # Go up to sugar examples root
sys.path.insert(0, str(parent_dir))

# Import the required modules
try:
    from backend.config import CLICKHOUSE_NATIVE_CONFIG
    print("Successfully imported database configuration")
except ImportError as e:
    print(f"Import attempt failed: {e}")
    CLICKHOUSE_NATIVE_CONFIG = None
    print("Import failed, setting config to None")

def main():
    """Main function to check recent predictions"""
    if not CLICKHOUSE_NATIVE_CONFIG:
        print("Database configuration not available")
        return 1
    
    client = Client(**CLICKHOUSE_NATIVE_CONFIG)
    
    try:
        # Check predictions from today
        today = datetime.now().date()
        print(f'=== Checking predictions from {today} ===')
        
        query = f"""
        SELECT 
            datetime,
            sentiment,
            prob_negative,
            prob_positive,
            prob_neutral,
            news_id,
            asset,
            created_at
        FROM sentiment_predictions 
        WHERE toDate(created_at) = toDate('{today}')
        ORDER BY created_at DESC
        """
        result = client.execute(query)
        columns = ['datetime', 'sentiment', 'prob_negative', 'prob_positive', 'prob_neutral', 'news_id', 'asset', 'created_at']
        df = pd.DataFrame(result, columns=columns)
        
        print(f"Found {len(df)} predictions from today")
        
        if not df.empty:
            print("\nSample predictions:")
            for i, row in df.head(10).iterrows():
                print(f"\nPrediction {i+1}:")
                print(f"  Created: {row['created_at']}")
                print(f"  Datetime: {row['datetime']}")
                print(f"  Sentiment: {row['sentiment']}")
                print(f"  Probabilities: neg={row['prob_negative']:.3f}, neu={row['prob_neutral']:.3f}, pos={row['prob_positive']:.3f}")
                print(f"  News ID: {row['news_id']}")
                print(f"  Asset: {row['asset']}")
        
        # Check predictions from the last 7 days
        print(f'\n=== Checking predictions from the last 7 days ===')
        week_ago = (datetime.now() - timedelta(days=7)).date()
        
        query = f"""
        SELECT 
            COUNT(*) as total_count,
            toDate(created_at) as prediction_date,
            groupArray(DISTINCT asset) as assets
        FROM sentiment_predictions 
        WHERE toDate(created_at) >= toDate('{week_ago}')
        GROUP BY toDate(created_at)
        ORDER BY prediction_date DESC
        """
        result = client.execute(query)
        
        print("Daily prediction counts:")
        for row in result:
            count, date, assets = row
            print(f"  {date}: {count} predictions, assets: {assets}")
        
        # Check all sugar predictions
        print(f'\n=== All sugar predictions ===')
        query = """
        SELECT 
            COUNT(*) as total_count,
            MIN(created_at) as earliest,
            MAX(created_at) as latest
        FROM sentiment_predictions 
        WHERE asset = 'Sugar'
        """
        result = client.execute(query)
        total_count, earliest, latest = result[0]
        print(f"Total sugar predictions: {total_count}")
        print(f"Earliest: {earliest}")
        print(f"Latest: {latest}")
        
        # Check if there are any predictions without asset specified
        print(f'\n=== Predictions without asset specified ===')
        query = """
        SELECT COUNT(*) 
        FROM sentiment_predictions 
        WHERE asset = '' OR asset IS NULL
        """
        result = client.execute(query)
        print(f"Predictions without asset: {result[0][0]}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
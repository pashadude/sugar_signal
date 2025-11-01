#!/usr/bin/env python3
"""
Script to debug data matching between source_of_truth and sentiment_predictions
"""

import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from clickhouse_driver import Client

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
    """Main function to debug data matching"""
    if not CLICKHOUSE_NATIVE_CONFIG:
        print("Database configuration not available")
        return 1
    
    client = Client(**CLICKHOUSE_NATIVE_CONFIG)
    
    try:
        # Get sample data from source_of_truth
        print('=== Sample data from news.source_of_truth (first 5 rows) ===')
        query = """
        SELECT 
            timestamp_created as datetime,
            source,
            commodity as asset,
            title,
            text
        FROM news.source_of_truth 
        WHERE commodity = 'Sugar' 
        ORDER BY timestamp_created DESC 
        LIMIT 5
        """
        result = client.execute(query)
        columns = ['datetime', 'source', 'asset', 'title', 'text']
        source_df = pd.DataFrame(result, columns=columns)
        
        for i, row in source_df.iterrows():
            print(f"\nRow {i+1}:")
            print(f"  Datetime: {row['datetime']}")
            print(f"  Source: {row['source']}")
            print(f"  Asset: {row['asset']}")
            print(f"  Title: {row['title'][:100]}...")
            print(f"  Text: {row['text'][:100]}...")
        
        # Get sample data from sentiment_predictions
        print('\n=== Sample data from sentiment_predictions (first 5 rows) ===')
        query = """
        SELECT 
            datetime,
            sentiment,
            prob_negative,
            prob_positive,
            prob_neutral,
            news_id,
            asset
        FROM sentiment_predictions 
        WHERE asset = 'Sugar'
        ORDER BY datetime DESC 
        LIMIT 5
        """
        result = client.execute(query)
        columns = ['datetime', 'sentiment', 'prob_negative', 'prob_positive', 'prob_neutral', 'news_id', 'asset']
        pred_df = pd.DataFrame(result, columns=columns)
        
        for i, row in pred_df.iterrows():
            print(f"\nRow {i+1}:")
            print(f"  Datetime: {row['datetime']}")
            print(f"  Sentiment: {row['sentiment']}")
            print(f"  Probabilities: neg={row['prob_negative']:.3f}, neu={row['prob_neutral']:.3f}, pos={row['prob_positive']:.3f}")
            print(f"  News ID: {row['news_id']}")
            print(f"  Asset: {row['asset']}")
        
        # Check if there are any common datetime ranges
        print('\n=== Checking datetime ranges ===')
        query = """
        SELECT 
            MIN(timestamp_created) as min_source_time,
            MAX(timestamp_created) as max_source_time
        FROM news.source_of_truth 
        WHERE commodity = 'Sugar'
        """
        result = client.execute(query)
        min_source_time, max_source_time = result[0]
        print(f"Source of truth time range: {min_source_time} to {max_source_time}")
        
        query = """
        SELECT 
            MIN(datetime) as min_pred_time,
            MAX(datetime) as max_pred_time
        FROM sentiment_predictions 
        WHERE asset = 'Sugar'
        """
        result = client.execute(query)
        min_pred_time, max_pred_time = result[0]
        print(f"Predictions time range: {min_pred_time} to {max_pred_time}")
        
        # Check total counts
        print('\n=== Total counts ===')
        query = "SELECT COUNT(*) FROM news.source_of_truth WHERE commodity = 'Sugar'"
        result = client.execute(query)
        print(f"Total source_of_truth records: {result[0][0]}")
        
        query = "SELECT COUNT(*) FROM sentiment_predictions WHERE asset = 'Sugar'"
        result = client.execute(query)
        print(f"Total sentiment_predictions records: {result[0][0]}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
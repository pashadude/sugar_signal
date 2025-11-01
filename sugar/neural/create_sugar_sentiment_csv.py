#!/usr/bin/env python3
"""
Script to create a comprehensive CSV with sugar articles from source_of_truth
and their sentiment predictions from sentiment_predictions table.
Output: id, datetime, asset, source, title, text, metadata, sentiment, prob_negative, prob_neutral, prob_positive
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import clickhouse_connect
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # Go up to sugar examples root
sys.path.insert(0, str(parent_dir))

# Import the required modules
try:
    from backend.config import CLICKHOUSE_CONFIG
    print("Successfully imported using relative path")
except ImportError as e:
    print(f"Import attempt failed: {e}")
    CLICKHOUSE_CONFIG = None
    print("Import failed, setting config to None")

def create_sugar_sentiment_csv():
    """Create CSV with sugar articles and their sentiment predictions."""
    
    print("=== Creating Complete Sugar Dataset CSV ===")
    
    if CLICKHOUSE_CONFIG is None:
        print("❌ Error: ClickHouse configuration not available")
        return False
    
    try:
        # Connect to ClickHouse
        print("Connecting to ClickHouse...")
        client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
        print("✓ Connected to ClickHouse successfully")
        
        # Get all sugar articles from news.news table (source of truth)
        print("Getting sugar articles from news.news...")
        source_query = """
        SELECT
            id,
            datetime,
            asset,
            source,
            title,
            text,
            metadata
        FROM news.news
        WHERE asset = 'Sugar'
        ORDER BY datetime DESC
        """
        
        source_result = client.query(source_query)
        print(f"Found {len(source_result.result_rows)} sugar articles in news.news")
        
        # Get all sentiment predictions for sugar articles
        print("Getting sentiment predictions for sugar articles...")
        predictions_query = """
        SELECT
            news_id,
            sentiment,
            prob_negative,
            prob_neutral,
            prob_positive
        FROM sentiment_predictions
        WHERE news_id IN (
            SELECT id
            FROM news.news
            WHERE asset = 'Sugar'
        )
        """
        
        predictions_result = client.query(predictions_query)
        print(f"Found {len(predictions_result.result_rows)} sentiment predictions for sugar articles")
        
        # Create DataFrames
        source_df = pd.DataFrame(source_result.result_rows, columns=[
            'id', 'datetime', 'asset', 'source', 'title', 'text', 'metadata'
        ])
        
        pred_df = pd.DataFrame(predictions_result.result_rows, columns=[
            'news_id', 'sentiment', 'prob_negative', 'prob_neutral', 'prob_positive'
        ])
        
        # Merge the data on id/news_id
        final_df = source_df.merge(pred_df, left_on='id', right_on='news_id', how='left')
        
        # Remove the news_id column as it's redundant
        final_df = final_df.drop(columns=['news_id'])
        
        # Convert datetime
        final_df['datetime'] = pd.to_datetime(final_df['datetime'])
        
        print(f"Final dataset has {len(final_df)} rows")
        print(f"Rows with predictions: {final_df['sentiment'].notna().sum()}")
        print(f"Rows missing predictions: {final_df['sentiment'].isna().sum()}")
        
        # Sort by datetime
        final_df = final_df.sort_values('datetime')
        
        # Save to CSV with the required filename
        output_file = '/Users/pauldudko/VSProjects/commodity_signal/ShinkaEvolve/shinka/examples/sugar/neural/sugar_complete_dataset_may2021_may2025.csv'
        final_df.to_csv(output_file, index=False)
        
        print(f"\n✓ CSV saved to: {output_file}")
        print(f"Total records: {len(final_df)}")
        print(f"Date range: {final_df['datetime'].min()} to {final_df['datetime'].max()}")
        
        # Show summary statistics
        print(f"\n=== Summary Statistics ===")
        print(f"Sentiment distribution:")
        if final_df['sentiment'].notna().sum() > 0:
            print(final_df['sentiment'].value_counts())
        else:
            print("No sentiment predictions available")
        
        if final_df['sentiment'].notna().sum() > 0:
            print(f"\nAverage probabilities:")
            print(f"Positive: {final_df['prob_positive'].mean():.3f}")
            print(f"Negative: {final_df['prob_negative'].mean():.3f}")
            print(f"Neutral: {final_df['prob_neutral'].mean():.3f}")
        
        # Show first few rows
        print(f"\n=== First 5 rows ===")
        print(final_df.head())
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Close connection
        if 'client' in locals():
            client.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    success = create_sugar_sentiment_csv()
    sys.exit(0 if success else 1)
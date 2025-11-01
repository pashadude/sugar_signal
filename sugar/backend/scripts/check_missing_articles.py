#!/usr/bin/env python3
"""
Script to check which sugar articles are missing predictions
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def main():
    print("=== CHECKING MISSING SUGAR ARTICLES ===")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        # Connect to database
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        print("✓ ClickHouse connection successful")
        
        # Get sugar articles without predictions
        query = """
        SELECT id, datetime, title, source
        FROM news.news 
        WHERE asset = 'Sugar' 
        AND id NOT IN (SELECT DISTINCT news_id FROM sentiment_predictions)
        ORDER BY datetime DESC
        """
        result = client.execute(query)
        missing_count = len(result)
        
        print(f"Sugar articles missing predictions: {missing_count}")
        print(f"\nFirst 10 missing articles:")
        for i, (news_id, datetime, title, source) in enumerate(result[:10]):
            print(f"  {i+1}. {news_id[:8]}... | {datetime} | {source} | {title[:50]}...")
        
        # Get sugar articles with predictions
        query = """
        SELECT id, datetime, title, source
        FROM news.news 
        WHERE asset = 'Sugar' 
        AND id IN (SELECT DISTINCT news_id FROM sentiment_predictions)
        ORDER BY datetime DESC
        """
        result = client.execute(query)
        with_predictions_count = len(result)
        
        print(f"\nSugar articles with predictions: {with_predictions_count}")
        print(f"\nFirst 10 articles with predictions:")
        for i, (news_id, datetime, title, source) in enumerate(result[:10]):
            print(f"  {i+1}. {news_id[:8]}... | {datetime} | {source} | {title[:50]}...")
        
        # Check date distribution of missing articles
        query = """
        SELECT 
            COUNT(*) as count,
            MIN(datetime) as earliest,
            MAX(datetime) as latest
        FROM news.news 
        WHERE asset = 'Sugar' 
        AND id NOT IN (SELECT DISTINCT news_id FROM sentiment_predictions)
        """
        result = client.execute(query)
        if result:
            count, earliest, latest = result[0]
            print(f"\nMissing articles date range:")
            print(f"  Count: {count}")
            print(f"  Earliest: {earliest}")
            print(f"  Latest: {latest}")
        
        # Close connection
        client.disconnect()
        print("✓ Database connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to check current sentiment predictions for sugar articles
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def main():
    print("=== CHECKING CURRENT SENTIMENT PREDICTIONS ===")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        # Connect to database
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        print("✓ ClickHouse connection successful")
        
        # Check current predictions count
        query = "SELECT COUNT(*) FROM sentiment_predictions WHERE news_id IN (SELECT id FROM news.news WHERE asset = 'Sugar')"
        result = client.execute(query)
        count = result[0][0]
        print(f"Current sentiment predictions for sugar articles: {count}")
        
        # Check date range of existing predictions
        query = "SELECT MIN(datetime), MAX(datetime) FROM sentiment_predictions WHERE news_id IN (SELECT id FROM news.news WHERE asset = 'Sugar')"
        result = client.execute(query)
        if result[0][0] and result[0][1]:
            print(f"Date range of existing predictions: {result[0][0]} to {result[0][1]}")
        
        # Check how many articles are missing predictions
        query = """
        SELECT COUNT(*) 
        FROM news.news 
        WHERE asset = 'Sugar' 
        AND id NOT IN (SELECT news_id FROM sentiment_predictions)
        """
        result = client.execute(query)
        missing = result[0][0]
        print(f"Sugar articles missing predictions: {missing}")
        
        # Close connection
        client.disconnect()
        print("✓ Database connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
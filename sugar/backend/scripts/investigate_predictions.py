#!/usr/bin/env python3
"""
Script to investigate the discrepancy between predictor output and database predictions
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def main():
    print("=== INVESTIGATING PREDICTION DISCREPANCY ===")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        # Connect to database
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        print("✓ ClickHouse connection successful")
        
        # Check total predictions in sentiment_predictions table
        query = "SELECT COUNT(*) FROM sentiment_predictions"
        result = client.execute(query)
        total_predictions = result[0][0]
        print(f"Total predictions in sentiment_predictions table: {total_predictions}")
        
        # Check predictions from today
        query = "SELECT COUNT(*) FROM sentiment_predictions WHERE toDateTime(created_at) >= today()"
        result = client.execute(query)
        today_predictions = result[0][0]
        print(f"Predictions created today: {today_predictions}")
        
        # Check predictions created in the last hour
        query = "SELECT COUNT(*) FROM sentiment_predictions WHERE created_at >= now() - interval 1 hour"
        result = client.execute(query)
        recent_predictions = result[0][0]
        print(f"Predictions created in the last hour: {recent_predictions}")
        
        # Check sugar articles with predictions using different query
        query = """
        SELECT COUNT(DISTINCT sp.news_id) 
        FROM sentiment_predictions sp
        JOIN news.news n ON sp.news_id = n.id
        WHERE n.asset = 'Sugar'
        """
        result = client.execute(query)
        sugar_with_predictions = result[0][0]
        print(f"Sugar articles with predictions (JOIN query): {sugar_with_predictions}")
        
        # Check the most recent predictions
        query = """
        SELECT sp.news_id, n.asset, sp.created_at, sp.sentiment
        FROM sentiment_predictions sp
        LEFT JOIN news.news n ON sp.news_id = n.id
        ORDER BY sp.created_at DESC
        LIMIT 10
        """
        result = client.execute(query)
        print(f"\nMost recent 10 predictions:")
        for row in result:
            news_id, asset, created_at, sentiment = row
            print(f"  - {news_id[:8]}... | Asset: {asset} | Created: {created_at} | Sentiment: {sentiment}")
        
        # Check if there are any predictions without matching news articles
        query = """
        SELECT COUNT(*) 
        FROM sentiment_predictions sp
        LEFT JOIN news.news n ON sp.news_id = n.id
        WHERE n.id IS NULL
        """
        result = client.execute(query)
        orphaned_predictions = result[0][0]
        print(f"\nOrphaned predictions (no matching news article): {orphaned_predictions}")
        
        # Check total sugar articles
        query = "SELECT COUNT(*) FROM news.news WHERE asset = 'Sugar'"
        result = client.execute(query)
        total_sugar = result[0][0]
        print(f"Total sugar articles in news.news: {total_sugar}")
        
        # Close connection
        client.disconnect()
        print("✓ Database connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
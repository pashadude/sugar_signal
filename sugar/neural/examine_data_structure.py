#!/usr/bin/env python3
"""
Script to examine the data structure and relationships between tables.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import clickhouse_connect

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

def examine_data_structure():
    """Examine the data structure and relationships between tables."""
    
    print("=== Examining Data Structure ===")
    
    if CLICKHOUSE_CONFIG is None:
        print("❌ Error: ClickHouse configuration not available")
        return False
    
    try:
        # Connect to ClickHouse
        print("Connecting to ClickHouse...")
        client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
        print("✓ Connected to ClickHouse successfully")
        
        # 1. Check news.news table structure and sample data
        print("\n1. Examining news.news table...")
        news_schema_query = "DESCRIBE TABLE news.news"
        news_schema_result = client.query(news_schema_query)
        print("news.news schema:")
        for row in news_schema_result.result_rows:
            print(f"  {row[0]}: {row[1]}")
        
        # Sample data from news.news
        news_sample_query = "SELECT * FROM news.news WHERE asset = 'Sugar' LIMIT 3"
        news_sample_result = client.query(news_sample_query)
        print("\nSample data from news.news:")
        for i, row in enumerate(news_sample_result.result_rows):
            print(f"  Row {i+1}: {row}")
        
        # 2. Check source_of_truth table structure and sample data
        print("\n2. Examining news.source_of_truth table...")
        source_schema_query = "DESCRIBE TABLE news.source_of_truth"
        source_schema_result = client.query(source_schema_query)
        print("news.source_of_truth schema:")
        for row in source_schema_result.result_rows:
            print(f"  {row[0]}: {row[1]}")
        
        # Sample data from source_of_truth
        source_sample_query = "SELECT * FROM news.source_of_truth WHERE commodity = 'Sugar' LIMIT 3"
        source_sample_result = client.query(source_sample_query)
        print("\nSample data from news.source_of_truth:")
        for i, row in enumerate(source_sample_result.result_rows):
            print(f"  Row {i+1}: {row}")
        
        # 3. Check sentiment_predictions table structure and sample data
        print("\n3. Examining sentiment_predictions table...")
        pred_schema_query = "DESCRIBE TABLE sentiment_predictions"
        pred_schema_result = client.query(pred_schema_query)
        print("sentiment_predictions schema:")
        for row in pred_schema_result.result_rows:
            print(f"  {row[0]}: {row[1]}")
        
        # Sample data from sentiment_predictions
        pred_sample_query = "SELECT * FROM sentiment_predictions LIMIT 3"
        pred_sample_result = client.query(pred_sample_query)
        print("\nSample data from sentiment_predictions:")
        for i, row in enumerate(pred_sample_result.result_rows):
            print(f"  Row {i+1}: {row}")
        
        # 4. Check relationships between tables
        print("\n4. Checking relationships between tables...")
        
        # Check if news.news has an id column that matches sentiment_predictions.news_id
        news_id_check = "SELECT id FROM news.news WHERE asset = 'Sugar' LIMIT 1"
        news_id_result = client.query(news_id_check)
        if news_id_result.result_rows:
            sample_news_id = news_id_result.first_row[0]
            print(f"Sample news.news ID: {sample_news_id}")
            
            # Check if this ID exists in sentiment_predictions
            pred_check = f"SELECT COUNT(*) FROM sentiment_predictions WHERE news_id = '{sample_news_id}'"
            pred_count_result = client.query(pred_check)
            pred_count = pred_count_result.first_row[0]
            print(f"Predictions for this ID: {pred_count}")
        
        # 5. Check date ranges
        print("\n5. Checking date ranges...")
        
        # news.news date range
        news_date_query = """
        SELECT 
            MIN(datetime) as min_date,
            MAX(datetime) as max_date,
            COUNT(*) as count
        FROM news.news 
        WHERE asset = 'Sugar'
        """
        news_date_result = client.query(news_date_query)
        news_min_date, news_max_date, news_count = news_date_result.first_row
        print(f"news.news sugar articles: {news_count} articles from {news_min_date} to {news_max_date}")
        
        # source_of_truth date range
        source_date_query = """
        SELECT 
            MIN(timestamp_created) as min_date,
            MAX(timestamp_created) as max_date,
            COUNT(*) as count
        FROM news.source_of_truth 
        WHERE commodity = 'Sugar'
        """
        source_date_result = client.query(source_date_query)
        source_min_date, source_max_date, source_count = source_date_result.first_row
        print(f"source_of_truth sugar articles: {source_count} articles from {source_min_date} to {source_max_date}")
        
        # sentiment_predictions date range
        pred_date_query = """
        SELECT 
            MIN(datetime) as min_date,
            MAX(datetime) as max_date,
            COUNT(*) as count
        FROM sentiment_predictions
        """
        pred_date_result = client.query(pred_date_query)
        pred_min_date, pred_max_date, pred_count = pred_date_result.first_row
        print(f"sentiment_predictions: {pred_count} predictions from {pred_min_date} to {pred_max_date}")
        
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
    success = examine_data_structure()
    sys.exit(0 if success else 1)
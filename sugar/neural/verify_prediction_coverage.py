#!/usr/bin/env python3
"""
Script to verify prediction coverage for sugar articles.
This checks how many sugar articles have sentiment predictions.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

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

import clickhouse_connect

def check_prediction_coverage():
    """Check how many sugar articles have sentiment predictions."""
    
    print("=== Verifying Sugar Article Prediction Coverage ===")
    
    # Check if config is available
    if CLICKHOUSE_CONFIG is None:
        print("❌ Error: ClickHouse configuration not available")
        return False
    
    try:
        # Connect to ClickHouse
        print("Connecting to ClickHouse...")
        client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
        print("✓ Connected to ClickHouse successfully")
        
        # Query 1: Count total sugar articles in news.news
        print("\n1. Counting total sugar articles in news.news...")
        total_query = """
        SELECT COUNT(*) as total_count
        FROM news.news
        WHERE asset = 'Sugar'
        """
        total_result = client.query(total_query)
        total_count = total_result.first_row[0]
        print(f"Total sugar articles in news.news: {total_count}")
        
        # Query 2: Count sugar articles with predictions
        print("\n2. Counting sugar articles with sentiment predictions...")
        prediction_query = """
        SELECT COUNT(DISTINCT news_id) as predicted_count
        FROM sentiment_predictions sp
        JOIN news.news n ON sp.news_id = n.id
        WHERE n.asset = 'Sugar'
        """
        prediction_result = client.query(prediction_query)
        predicted_count = prediction_result.first_row[0]
        print(f"Sugar articles with predictions: {predicted_count}")
        
        # Query 3: Check date range
        print("\n3. Checking date range for sugar articles...")
        date_query = """
        SELECT
            MIN(datetime) as min_date,
            MAX(datetime) as max_date,
            COUNT(*) as count
        FROM news.news
        WHERE asset = 'Sugar'
        """
        date_result = client.query(date_query)
        min_date, max_date, count = date_result.first_row
        print(f"Date range: {min_date} to {max_date}")
        print(f"Total articles in date range: {count}")
        
        # Query 4: Check if there are predictions in source_of_truth table
        print("\n4. Checking news.source_of_truth table for sugar data...")
        source_query = """
        SELECT COUNT(*) as source_count
        FROM news.source_of_truth
        WHERE commodity = 'Sugar'
        """
        try:
            source_result = client.query(source_query)
            source_count = source_result.first_row[0]
            print(f"Sugar articles in source_of_truth: {source_count}")
        except Exception as e:
            print(f"Error querying source_of_truth: {e}")
            source_count = 0
        
        # Summary
        print("\n=== SUMMARY ===")
        print(f"Total sugar articles: {total_count}")
        print(f"Articles with predictions: {predicted_count}")
        print(f"Coverage: {predicted_count/total_count*100:.1f}%")
        print(f"Missing predictions: {total_count - predicted_count}")
        
        if predicted_count < total_count:
            print(f"\n⚠️  WARNING: {total_count - predicted_count} sugar articles are missing predictions!")
            print("Need to run sugar predictor again for remaining articles.")
            return False
        else:
            print("\n✓ All sugar articles have predictions!")
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
    success = check_prediction_coverage()
    sys.exit(0 if success else 1)
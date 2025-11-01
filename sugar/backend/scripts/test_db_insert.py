#!/usr/bin/env python3
"""
Script to test database insertion for sentiment predictions
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def main():
    print("=== TESTING DATABASE INSERTION ===")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        # Connect to database
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        print("✓ ClickHouse connection successful")
        
        # Test 1: Check if we can read from sentiment_predictions
        query = "SELECT COUNT(*) FROM sentiment_predictions"
        result = client.execute(query)
        total_count = result[0][0]
        print(f"1. Total predictions in database: {total_count}")
        
        # Test 2: Try to insert a test prediction
        test_prediction = {
            'datetime': datetime.now(),
            'news_id': 'test_article_12345',
            'prompt_id': '7a603cf48e9e05d2',
            'model': "Qwen/Qwen2.5-72B-Instruct",
            'sentiment': 'positive',
            'prob_negative': 0.1,
            'prob_neutral': 0.2,
            'prob_positive': 0.7,
            'created_at': datetime.now()
        }
        
        print("2. Attempting to insert test prediction...")
        
        record = (
            test_prediction['datetime'],
            test_prediction['news_id'],
            test_prediction['prompt_id'],
            test_prediction['model'],
            test_prediction['sentiment'],
            test_prediction['prob_negative'],
            test_prediction['prob_neutral'],
            test_prediction['prob_positive'],
            test_prediction['created_at']
        )
        
        try:
            client.execute(
                '''INSERT INTO sentiment_predictions 
                   (datetime, news_id, prompt_id, model, sentiment, 
                    prob_negative, prob_neutral, prob_positive, created_at) VALUES''',
                [record]
            )
            print("✓ Test prediction inserted successfully")
            
            # Verify insertion
            query = "SELECT COUNT(*) FROM sentiment_predictions WHERE news_id = 'test_article_12345'"
            result = client.execute(query)
            test_count = result[0][0]
            print(f"✓ Verification: Found {test_count} test prediction(s)")
            
            # Clean up test record
            query = "ALTER TABLE sentiment_predictions DELETE WHERE news_id = 'test_article_12345'"
            client.execute(query)
            print("✓ Test record cleaned up")
            
        except Exception as e:
            print(f"✗ Insertion failed: {e}")
            return False
        
        # Test 3: Check table schema
        query = "DESCRIBE TABLE sentiment_predictions"
        result = client.execute(query)
        print(f"\n3. Table schema:")
        for column in result:
            print(f"   - {column[0]}: {column[1]}")
        
        # Close connection
        client.disconnect()
        print("✓ Database connection closed")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Database insertion test passed!")
    else:
        print("\n❌ Database insertion test failed!")
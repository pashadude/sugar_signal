#!/usr/bin/env python3
"""
Test script to verify that the fixed predictor can now fetch all 267 sugar articles
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def test_fixed_query():
    """Test the fixed query logic"""
    print("=== TESTING FIXED PREDICTOR QUERY ===")
    print(f"Started at: {datetime.now()}")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        print(f"Connecting to ClickHouse at {CLICKHOUSE_NATIVE_CONFIG['host']}:{CLICKHOUSE_NATIVE_CONFIG['port']}")
        
        # Test connection
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        
        # Execute a simple query to test connectivity
        result = client.execute('SELECT 1 as test')
        
        if result and result[0][0] == 1:
            print("✓ ClickHouse connection successful")
        else:
            print("✗ ClickHouse connection failed")
            return False
            
    except Exception as e:
        print(f"✗ ClickHouse connection failed: {e}")
        return False
    
    # Test 1: Query without date filtering (new default behavior)
    print("\n=== TEST 1: Query without date filtering (new default) ===")
    try:
        end_date = datetime.now()
        
        query1 = f"""
        WITH deduplicated_articles AS (
            SELECT 
                id,
                title,
                text,
                source,
                asset,
                metadata,
                datetime,
                ROW_NUMBER() OVER (PARTITION BY title, source ORDER BY datetime DESC) as rn
            FROM news.news 
            WHERE asset = 'Sugar'
            AND datetime <= '{end_date.strftime('%Y-%m-%d')}'
            AND length(text) > 100
        )
        SELECT COUNT(*)
        FROM deduplicated_articles d
        WHERE d.rn = 1
        """
        result1 = client.execute(query1)
        count1 = result1[0][0]
        print(f"Query result: {count1} articles")
        
        if count1 == 265:  # Expected after deduplication (267 - 2 duplicates)
            print("✓ SUCCESS: Fixed query returns expected 265 articles (after deduplication)")
            test1_passed = True
        else:
            print(f"✗ FAILED: Expected 265 articles, got {count1}")
            test1_passed = False
            
    except Exception as e:
        print(f"✗ Error executing test 1: {e}")
        test1_passed = False
    
    # Test 2: Query with explicit date filtering (old behavior)
    print("\n=== TEST 2: Query with 400-day date filtering (old behavior) ===")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=400)
        
        query2 = f"""
        WITH deduplicated_articles AS (
            SELECT 
                id,
                title,
                text,
                source,
                asset,
                metadata,
                datetime,
                ROW_NUMBER() OVER (PARTITION BY title, source ORDER BY datetime DESC) as rn
            FROM news.news 
            WHERE asset = 'Sugar'
            AND datetime >= '{start_date.strftime('%Y-%m-%d')}'
            AND datetime <= '{end_date.strftime('%Y-%m-%d')}'
            AND length(text) > 100
        )
        SELECT COUNT(*)
        FROM deduplicated_articles d
        WHERE d.rn = 1
        """
        result2 = client.execute(query2)
        count2 = result2[0][0]
        print(f"Query result: {count2} articles")
        
        if count2 == 5:
            print("✓ SUCCESS: 400-day filter still returns 5 articles (as expected)")
            test2_passed = True
        else:
            print(f"✗ FAILED: Expected 5 articles with 400-day filter, got {count2}")
            test2_passed = False
            
    except Exception as e:
        print(f"✗ Error executing test 2: {e}")
        test2_passed = False
    
    # Test 3: Test the actual function from the fixed predictor
    print("\n=== TEST 3: Test actual get_all_articles_for_prediction function ===")
    try:
        # Import the function from the fixed predictor
        sys.path.insert(0, str(project_root / 'shinka' / 'examples' / 'sugar' / 'neural'))
        from predict_sugar_sentiment_v2 import get_all_articles_for_prediction
        
        # Test with no date filtering (default)
        articles_no_filter = get_all_articles_for_prediction(client, 'Sugar', 'test_prompt_id')
        count_no_filter = len(articles_no_filter)
        print(f"Function result (no date filter): {count_no_filter} articles")
        
        # Test with date filtering
        articles_with_filter = get_all_articles_for_prediction(client, 'Sugar', 'test_prompt_id', days_back=400)
        count_with_filter = len(articles_with_filter)
        print(f"Function result (400-day filter): {count_with_filter} articles")
        
        if count_no_filter == 265 and count_with_filter == 5:
            print("✓ SUCCESS: Function works correctly with both scenarios")
            test3_passed = True
        else:
            print(f"✗ FAILED: Expected 265 and 5 articles, got {count_no_filter} and {count_with_filter}")
            test3_passed = False
            
    except Exception as e:
        print(f"✗ Error executing test 3: {e}")
        test3_passed = False
    
    # Summary
    print("\n=== TEST SUMMARY ===")
    all_passed = test1_passed and test2_passed and test3_passed
    
    print(f"Test 1 (no date filter): {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Test 2 (400-day filter): {'PASSED' if test2_passed else 'FAILED'}")
    print(f"Test 3 (function test): {'PASSED' if test3_passed else 'FAILED'}")
    print(f"Overall: {'PASSED' if all_passed else 'FAILED'}")
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! The fix is working correctly.")
        print("The predictor should now be able to process all 265 sugar articles (after deduplication).")
    else:
        print("\n❌ SOME TESTS FAILED. The fix needs further investigation.")
    
    # Close connection
    try:
        client.disconnect()
        print("✓ Database connection closed")
    except:
        pass
    
    return all_passed

if __name__ == "__main__":
    success = test_fixed_query()
    exit(0 if success else 1)
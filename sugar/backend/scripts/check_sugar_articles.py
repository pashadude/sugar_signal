#!/usr/bin/env python3
"""
Script to check the actual count of sugar articles in the database
and investigate the discrepancy between expected (267) and found (5) articles
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def main():
    print("=== SUGAR ARTICLE INVESTIGATION ===")
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
            return
            
    except Exception as e:
        print(f"✗ ClickHouse connection failed: {e}")
        return
    
    # Query 1: Basic count of sugar articles
    print("\n=== QUERY 1: Basic sugar article count ===")
    try:
        query1 = "SELECT COUNT(*) FROM news.news WHERE asset = 'Sugar'"
        result1 = client.execute(query1)
        count1 = result1[0][0]
        print(f"Query: {query1}")
        print(f"Result: {count1} sugar articles")
    except Exception as e:
        print(f"Error executing query 1: {e}")
        count1 = 0
    
    # Query 2: Check for variations in asset name
    print("\n=== QUERY 2: Sugar asset name variations ===")
    try:
        query2 = "SELECT DISTINCT asset FROM news.news WHERE asset ILIKE '%sugar%'"
        result2 = client.execute(query2)
        print(f"Query: {query2}")
        print("Asset variations containing 'sugar':")
        for row in result2:
            print(f"  - '{row[0]}'")
    except Exception as e:
        print(f"Error executing query 2: {e}")
    
    # Query 3: Count with case-insensitive search
    print("\n=== QUERY 3: Case-insensitive sugar article count ===")
    try:
        query3 = "SELECT COUNT(*) FROM news.news WHERE asset ILIKE '%sugar%'"
        result3 = client.execute(query3)
        count3 = result3[0][0]
        print(f"Query: {query3}")
        print(f"Result: {count3} articles with asset ILIKE '%sugar%'")
    except Exception as e:
        print(f"Error executing query 3: {e}")
        count3 = 0
    
    # Query 4: Check date range distribution
    print("\n=== QUERY 4: Sugar articles by date range ===")
    try:
        query4 = """
        SELECT 
            COUNT(*) as total_articles,
            MIN(datetime) as earliest_date,
            MAX(datetime) as latest_date
        FROM news.news 
        WHERE asset = 'Sugar'
        """
        result4 = client.execute(query4)
        if result4:
            total, earliest, latest = result4[0]
            print(f"Query: {query4}")
            print(f"Total articles: {total}")
            print(f"Earliest date: {earliest}")
            print(f"Latest date: {latest}")
            
            if earliest and latest:
                days_span = (latest - earliest).days
                print(f"Date span: {days_span} days")
    except Exception as e:
        print(f"Error executing query 4: {e}")
    
    # Query 5: Check articles in last 400 days (current predictor setting)
    print("\n=== QUERY 5: Sugar articles in last 400 days ===")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=400)
        
        query5 = f"""
        SELECT COUNT(*) 
        FROM news.news 
        WHERE asset = 'Sugar'
        AND datetime >= '{start_date.strftime('%Y-%m-%d')}'
        AND datetime <= '{end_date.strftime('%Y-%m-%d')}'
        """
        result5 = client.execute(query5)
        count5 = result5[0][0]
        print(f"Query: {query5}")
        print(f"Result: {count5} sugar articles in last 400 days")
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error executing query 5: {e}")
        count5 = 0
    
    # Query 6: Check text length distribution
    print("\n=== QUERY 6: Sugar articles by text length ===")
    try:
        query6 = """
        SELECT 
            COUNT(*) as total_articles,
            COUNT(CASE WHEN length(text) <= 100 THEN 1 END) as very_short,
            COUNT(CASE WHEN length(text) > 100 AND length(text) <= 500 THEN 1 END) as short,
            COUNT(CASE WHEN length(text) > 500 AND length(text) <= 1000 THEN 1 END) as medium,
            COUNT(CASE WHEN length(text) > 1000 THEN 1 END) as long
        FROM news.news 
        WHERE asset = 'Sugar'
        """
        result6 = client.execute(query6)
        if result6:
            total, very_short, short, medium, long = result6[0]
            print(f"Query: {query6}")
            print(f"Total articles: {total}")
            print(f"Very short (<=100 chars): {very_short}")
            print(f"Short (101-500 chars): {short}")
            print(f"Medium (501-1000 chars): {medium}")
            print(f"Long (>1000 chars): {long}")
            
            # Check how many would be filtered by length > 100
            filtered_by_length = total - (very_short if total > 0 else 0)
            print(f"Articles that would pass length > 100 filter: {filtered_by_length}")
    except Exception as e:
        print(f"Error executing query 6: {e}")
    
    # Query 7: Check deduplication impact
    print("\n=== QUERY 7: Deduplication impact analysis ===")
    try:
        query7 = """
        WITH deduplicated_articles AS (
            SELECT 
                id,
                title,
                source,
                ROW_NUMBER() OVER (PARTITION BY title, source ORDER BY datetime DESC) as rn
            FROM news.news 
            WHERE asset = 'Sugar'
        )
        SELECT 
            COUNT(*) as total_before_deduplication,
            COUNT(CASE WHEN rn = 1 THEN 1 END) as total_after_deduplication,
            COUNT(CASE WHEN rn > 1 THEN 1 END) as duplicates_removed
        FROM deduplicated_articles
        """
        result7 = client.execute(query7)
        if result7:
            total_before, total_after, duplicates = result7[0]
            print(f"Query: {query7}")
            print(f"Total before deduplication: {total_before}")
            print(f"Total after deduplication: {total_after}")
            print(f"Duplicates that would be removed: {duplicates}")
            
            if total_before > 0:
                dup_percentage = (duplicates / total_before) * 100
                print(f"Duplicate percentage: {dup_percentage:.1f}%")
    except Exception as e:
        print(f"Error executing query 7: {e}")
    
    # Query 8: Simulate the exact query from the predictor
    print("\n=== QUERY 8: Simulate exact predictor query ===")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=400)
        
        query8 = f"""
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
        result8 = client.execute(query8)
        count8 = result8[0][0]
        print(f"Query: {query8}")
        print(f"Result: {count8} articles (this should match the predictor's count)")
        print(f"This is the exact query used by the predictor!")
    except Exception as e:
        print(f"Error executing query 8: {e}")
        count8 = 0
    
    # Summary
    print("\n=== INVESTIGATION SUMMARY ===")
    print(f"Expected sugar articles: 267")
    print(f"Basic count (asset = 'Sugar'): {count1}")
    print(f"Case-insensitive count (ILIKE '%sugar%'): {count3}")
    print(f"Last 400 days count: {count5}")
    print(f"Predictor query simulation result: {count8}")
    
    if count8 == 5:
        print("\n🔍 ISSUE CONFIRMED: The predictor query is indeed only finding 5 articles!")
        print("This matches the reported issue. Now we need to identify which filter is causing the problem.")
        
        if count1 == 267:
            print("✓ The basic count matches expected 267 articles")
            print("✗ The issue is in the predictor's filtering logic")
            
            if count5 < count1:
                print(f"⚠️  Date filter (400 days) is removing {count1 - count5} articles")
            
            if count8 < count5:
                print(f"⚠️  Other filters (length + deduplication) are removing {count5 - count8} articles")
        else:
            print(f"⚠️  Basic count ({count1}) doesn't match expected 267 articles")
            print("The issue might be with the expected count or asset naming")
    else:
        print(f"\n🤔 UNEXPECTED: Predictor simulation found {count8} articles, but the issue reported 5 articles")
        print("This suggests the problem might be elsewhere or the data has changed")
    
    # Close connection
    try:
        client.disconnect()
        print("✓ Database connection closed")
    except:
        pass

if __name__ == "__main__":
    main()
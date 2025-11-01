#!/usr/bin/env python3
"""
Script to check exact prediction counts and identify any issues
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def main():
    print("=== DETAILED PREDICTION COUNT ANALYSIS ===")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        # Connect to database
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        print("✓ ClickHouse connection successful")
        
        # Check 1: Count all predictions for sugar articles
        query = """
        SELECT COUNT(*) 
        FROM sentiment_predictions 
        WHERE news_id IN (SELECT id FROM news.news WHERE asset = 'Sugar')
        """
        result = client.execute(query)
        count1 = result[0][0]
        print(f"1. Direct count of predictions for sugar articles: {count1}")
        
        # Check 2: Count using JOIN
        query = """
        SELECT COUNT(DISTINCT sp.news_id) 
        FROM sentiment_predictions sp
        JOIN news.news n ON sp.news_id = n.id
        WHERE n.asset = 'Sugar'
        """
        result = client.execute(query)
        count2 = result[0][0]
        print(f"2. JOIN count of unique sugar articles with predictions: {count2}")
        
        # Check 3: Count total predictions created today for sugar
        query = """
        SELECT COUNT(*) 
        FROM sentiment_predictions sp
        JOIN news.news n ON sp.news_id = n.id
        WHERE n.asset = 'Sugar'
        AND toDateTime(sp.created_at) = today()
        """
        result = client.execute(query)
        count3 = result[0][0]
        print(f"3. Sugar predictions created today: {count3}")
        
        # Check 4: Count unique sugar articles that got predictions today
        query = """
        SELECT COUNT(DISTINCT sp.news_id) 
        FROM sentiment_predictions sp
        JOIN news.news n ON sp.news_id = n.id
        WHERE n.asset = 'Sugar'
        AND toDateTime(sp.created_at) = today()
        """
        result = client.execute(query)
        count4 = result[0][0]
        print(f"4. Unique sugar articles with predictions created today: {count4}")
        
        # Check 5: Look for duplicate predictions (same news_id, different timestamps)
        query = """
        SELECT news_id, COUNT(*) as prediction_count
        FROM sentiment_predictions 
        WHERE news_id IN (SELECT id FROM news.news WHERE asset = 'Sugar')
        GROUP BY news_id
        HAVING COUNT(*) > 1
        ORDER BY prediction_count DESC
        LIMIT 10
        """
        result = client.execute(query)
        print(f"\n5. Sugar articles with multiple predictions:")
        if result:
            for news_id, count in result:
                print(f"   - {news_id[:8]}...: {count} predictions")
        else:
            print("   - No duplicate predictions found")
        
        # Check 6: Get the actual list of sugar article IDs that have predictions
        query = """
        SELECT DISTINCT n.id, n.datetime
        FROM sentiment_predictions sp
        JOIN news.news n ON sp.news_id = n.id
        WHERE n.asset = 'Sugar'
        ORDER BY n.datetime DESC
        """
        result = client.execute(query)
        print(f"\n6. Sugar articles with predictions (showing first 20):")
        for i, (news_id, datetime) in enumerate(result[:20]):
            print(f"   - {news_id[:8]}... | {datetime}")
        
        # Check 7: Count sugar articles without predictions
        query = """
        SELECT COUNT(*) 
        FROM news.news 
        WHERE asset = 'Sugar' 
        AND id NOT IN (SELECT DISTINCT news_id FROM sentiment_predictions)
        """
        result = client.execute(query)
        count7 = result[0][0]
        print(f"\n7. Sugar articles without any predictions: {count7}")
        
        # Check 8: Total sugar articles
        query = "SELECT COUNT(*) FROM news.news WHERE asset = 'Sugar'"
        result = client.execute(query)
        count8 = result[0][0]
        print(f"8. Total sugar articles: {count8}")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        print(f"Total sugar articles: {count8}")
        print(f"Sugar articles with predictions: {count2}")
        print(f"Sugar articles without predictions: {count7}")
        print(f"Predictions created today: {count3}")
        print(f"Unique articles processed today: {count4}")
        
        if count2 + count7 == count8:
            print("✓ Counts add up correctly!")
        else:
            print(f"✗ Count discrepancy: {count2} + {count7} != {count8}")
        
        # Close connection
        client.disconnect()
        print("✓ Database connection closed")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to check for articles containing sugar-related keywords in title or text
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from clickhouse_driver import Client

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import configuration
try:
    from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
except ImportError:
    print("Error: Could not import ClickHouse configuration")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)

def connect_to_clickhouse():
    """Connect to ClickHouse database"""
    try:
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        # Test connection
        client.execute("SELECT 1")
        print("✓ Successfully connected to ClickHouse database")
        return client
    except Exception as e:
        print(f"✗ Error connecting to ClickHouse: {e}")
        return None

def check_sugar_keywords(client):
    """Check for articles containing sugar-related keywords"""
    try:
        # Define sugar-related keywords (same as in retrieve_sugar_news.py)
        sugar_keywords = [
            'sugar', 'sugarcane', 'sugar beet', 'sugar production', 
            'sugar price', 'sugar market', 'sugar export', 'sugar import',
            'sugar trading', 'sugar futures', 'sugar commodity', 'raw sugar',
            'white sugar', 'sugar refinery', 'sugar industry', 'sugar crop'
        ]
        
        # Build keyword conditions for title and text
        keyword_conditions = " OR ".join([
            f"LOWER(title) LIKE '%{keyword}%'" for keyword in sugar_keywords
        ] + [
            f"LOWER(text) LIKE '%{keyword}%'" for keyword in sugar_keywords
        ])
        
        # Count articles with sugar keywords in title or text
        count_query = f"""
        SELECT COUNT(*) as count
        FROM news.news
        WHERE {keyword_conditions}
        """
        
        count_result = client.execute(count_query)
        keyword_count = count_result[0][0] if count_result else 0
        print(f"\nArticles with sugar keywords in title or text: {keyword_count}")
        
        if keyword_count > 0:
            # Show sample articles with sugar keywords
            sample_query = f"""
            SELECT id, datetime, source, title, asset
            FROM news.news
            WHERE {keyword_conditions}
            ORDER BY datetime DESC
            LIMIT 10
            """
            
            sample_result = client.execute(sample_query)
            print("\n=== SAMPLE ARTICLES WITH SUGAR KEYWORDS ===")
            for i, (id, datetime, source, title, asset) in enumerate(sample_result, 1):
                print(f"{i}. ID: {id}")
                print(f"   Date: {datetime}")
                print(f"   Source: {source}")
                print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                print(f"   Asset: {asset}")
                print()
            
            # Check asset distribution among articles with sugar keywords
            asset_dist_query = f"""
            SELECT asset, COUNT(*) as count
            FROM news.news
            WHERE {keyword_conditions}
            GROUP BY asset
            ORDER BY count DESC
            """
            
            asset_dist_result = client.execute(asset_dist_query)
            print("\n=== ASSET DISTRIBUTION FOR ARTICLES WITH SUGAR KEYWORDS ===")
            for asset, count in asset_dist_result:
                print(f"{asset}: {count} articles")
        
        return True
        
    except Exception as e:
        print(f"Error checking sugar keywords: {e}")
        return False

def main():
    """Main function"""
    print("=== Sugar Keywords Check ===")
    print(f"Started at: {datetime.now()}")
    
    # Connect to database
    client = connect_to_clickhouse()
    if not client:
        sys.exit(1)
    
    try:
        # Check for sugar keywords
        success = check_sugar_keywords(client)
        
        if success:
            print("\n=== COMPLETED ===")
        else:
            print("\n=== FAILED ===")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()
        print("\nDisconnected from ClickHouse database")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to check the distribution of assets in the news.news database
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

def check_asset_distribution(client):
    """Check the distribution of assets in the database"""
    try:
        # Get all unique assets and their counts
        query = """
        SELECT asset, COUNT(*) as count
        FROM news.news
        GROUP BY asset
        ORDER BY count DESC
        """
        
        result = client.execute(query)
        print("\n=== ASSET DISTRIBUTION ===")
        total_count = 0
        for asset, count in result:
            print(f"{asset}: {count} articles")
            total_count += count
        
        print(f"\nTotal articles: {total_count}")
        
        # Check for articles containing 'sugar' in any case
        sugar_like_query = """
        SELECT COUNT(*) as count
        FROM news.news
        WHERE lower(asset) LIKE '%sugar%'
        """
        
        sugar_like_result = client.execute(sugar_like_query)
        sugar_like_count = sugar_like_result[0][0] if sugar_like_result else 0
        print(f"\nArticles with 'sugar' in asset (case insensitive): {sugar_like_count}")
        
        # Check for exact match 'Sugar'
        exact_sugar_query = """
        SELECT COUNT(*) as count
        FROM news.news
        WHERE asset = 'Sugar'
        """
        
        exact_sugar_result = client.execute(exact_sugar_query)
        exact_sugar_count = exact_sugar_result[0][0] if exact_sugar_result else 0
        print(f"Articles with exact asset 'Sugar': {exact_sugar_count}")
        
        # Show sample articles with different asset values
        sample_query = """
        SELECT id, datetime, source, title, asset
        FROM news.news
        ORDER BY datetime DESC
        LIMIT 10
        """
        
        sample_result = client.execute(sample_query)
        print("\n=== SAMPLE ARTICLES ===")
        for i, (id, datetime, source, title, asset) in enumerate(sample_result, 1):
            print(f"{i}. ID: {id}")
            print(f"   Date: {datetime}")
            print(f"   Source: {source}")
            print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
            print(f"   Asset: {asset}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Error checking asset distribution: {e}")
        return False

def main():
    """Main function"""
    print("=== Asset Distribution Check ===")
    print(f"Started at: {datetime.now()}")
    
    # Connect to database
    client = connect_to_clickhouse()
    if not client:
        sys.exit(1)
    
    try:
        # Check asset distribution
        success = check_asset_distribution(client)
        
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
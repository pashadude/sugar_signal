#!/usr/bin/env python3
"""
Script to delete all sugar news articles from ClickHouse database
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

def count_sugar_articles(client):
    """Count sugar-related articles in the database"""
    try:
        # Count articles with asset='Sugar' (exact match as used in sugar_news_fetcher.py)
        query = """
        SELECT COUNT(*) as total_articles
        FROM news.news
        WHERE asset = 'Sugar'
        """
        
        result = client.execute(query)
        count = result[0][0] if result else 0
        return count
    except Exception as e:
        print(f"Error counting sugar articles: {e}")
        return 0

def count_sugar_keyword_articles(client):
    """Count articles containing sugar-related keywords in title or text"""
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
        query = f"""
        SELECT COUNT(*) as total_articles
        FROM news.news
        WHERE {keyword_conditions}
        """
        
        result = client.execute(query)
        count = result[0][0] if result else 0
        return count
    except Exception as e:
        print(f"Error counting sugar keyword articles: {e}")
        return 0

def delete_sugar_articles(client, dry_run=True):
    """Delete sugar-related articles from the database"""
    try:
        if dry_run:
            print("\n=== DRY RUN MODE ===")
            print("No articles will be deleted. This is a preview only.")
        
        # First, let's see what we're about to delete
        preview_query = """
        SELECT id, datetime, source, title, asset
        FROM news.news
        WHERE asset = 'Sugar'
        ORDER BY datetime DESC
        LIMIT 5
        """
        
        preview_results = client.execute(preview_query)
        
        if preview_results:
            print(f"\nSample articles that would be deleted:")
            for i, (id, datetime, source, title, asset) in enumerate(preview_results, 1):
                print(f"{i}. ID: {id}")
                print(f"   Date: {datetime}")
                print(f"   Source: {source}")
                print(f"   Title: {title[:100]}{'...' if len(title) > 100 else ''}")
                print(f"   Asset: {asset}")
                print()
        else:
            print("No sugar articles found in the database")
            return 0
        
        # Count total articles to be deleted
        count = count_sugar_articles(client)
        print(f"Total sugar articles to be deleted: {count}")
        
        if dry_run:
            print("\n=== DRY RUN COMPLETE ===")
            print("Run with --execute to actually delete the articles")
            return count
        
        # Confirm deletion
        if not dry_run:
            confirm = input(f"\nAre you sure you want to delete {count} sugar articles? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Deletion cancelled")
                return 0
        
        # Perform deletion
        delete_query = """
        ALTER TABLE news.news
        DELETE WHERE asset = 'Sugar'
        """
        
        print("Deleting sugar articles...")
        result = client.execute(delete_query)
        
        print(f"✓ Successfully deleted sugar articles")
        return count
        
    except Exception as e:
        print(f"Error deleting sugar articles: {e}")
        return 0

def main():
    """Main function"""
    print("=== Sugar News Articles Deletion Tool ===")
    print(f"Started at: {datetime.now()}")
    
    # Parse command line arguments
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        dry_run = False
    
    # Connect to database
    client = connect_to_clickhouse()
    if not client:
        sys.exit(1)
    
    try:
        # Count current sugar articles
        count = count_sugar_articles(client)
        print(f"Current sugar articles in database: {count}")
        
        if count == 0:
            print("No sugar articles found with asset='Sugar'.")
            
            # Check if there are articles with sugar keywords but different asset values
            keyword_count = count_sugar_keyword_articles(client)
            if keyword_count > 0:
                print(f"\nHowever, found {keyword_count} articles containing sugar-related keywords in title or text.")
                print("These articles have different asset values (not 'Sugar').")
                print("\nPossible reasons:")
                print("1. The sugar news fetcher hasn't been run yet to assign 'Sugar' asset to articles")
                print("2. Articles were processed but failed the triage filter and were assigned 'General' asset")
                print("3. Articles were saved with a different asset value due to a configuration issue")
                print("\nTo see these articles, run: python retrieve_sugar_news.py")
            else:
                print("No articles with sugar-related keywords found either.")
                print("The database may not contain any sugar-related news articles.")
            return
        
        # Delete articles
        deleted_count = delete_sugar_articles(client, dry_run=dry_run)
        
        if not dry_run and deleted_count > 0:
            # Verify deletion
            remaining_count = count_sugar_articles(client)
            print(f"\nVerification:")
            print(f"Articles before deletion: {count}")
            print(f"Articles deleted: {deleted_count}")
            print(f"Articles remaining: {remaining_count}")
            
            if remaining_count == 0:
                print("✓ All sugar articles successfully deleted")
            else:
                print(f"⚠ {remaining_count} sugar articles still remain")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()
        print("\nDisconnected from ClickHouse database")

if __name__ == "__main__":
    main()
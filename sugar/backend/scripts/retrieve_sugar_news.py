#!/usr/bin/env python3
"""
Script to retrieve the last 10 articles about sugar from the news.news database
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def retrieve_sugar_articles():
    """Retrieve the last 10 articles about sugar from the news.news database"""
    print("Retrieving sugar articles from ClickHouse database...")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        print(f"Connecting to ClickHouse at {CLICKHOUSE_NATIVE_CONFIG['host']}:{CLICKHOUSE_NATIVE_CONFIG['port']}")
        
        # Connect to the database
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        
        # Define sugar-related keywords
        sugar_keywords = [
            'sugar', 'sugarcane', 'sugar beet', 'sugar production', 
            'sugar price', 'sugar market', 'sugar export', 'sugar import',
            'sugar trading', 'sugar futures', 'sugar commodity', 'raw sugar',
            'white sugar', 'sugar refinery', 'sugar industry', 'sugar crop'
        ]
        
        # Build the query to find articles where asset = 'Sugar' OR title/text contains sugar keywords
        keyword_conditions = " OR ".join([
            f"LOWER(title) LIKE '%{keyword}%'" for keyword in sugar_keywords
        ] + [
            f"LOWER(text) LIKE '%{keyword}%'" for keyword in sugar_keywords
        ])
        
        query = f"""
        SELECT id, datetime, source, title, text, asset, created_at
        FROM news.news 
        WHERE asset = 'Sugar' OR {keyword_conditions}
        ORDER BY datetime DESC
        LIMIT 10
        """
        
        print("Executing query...")
        articles = client.execute(query)
        
        if not articles:
            print("No sugar-related articles found in the database.")
            return []
        
        print(f"Found {len(articles)} sugar-related articles")
        
        # Convert to a more readable format
        result_articles = []
        for article in articles:
            article_id, article_datetime, source, title, text, asset, created_at = article
            
            # Create a snippet of the text (first 200 characters)
            text_snippet = text[:200] + "..." if len(text) > 200 else text
            
            result_articles.append({
                'id': article_id,
                'datetime': article_datetime,
                'source': source,
                'title': title,
                'text_snippet': text_snippet,
                'asset': asset,
                'created_at': created_at
            })
        
        # Close the connection
        client.disconnect()
        print("Database connection closed")
        
        return result_articles
        
    except Exception as e:
        print(f"Error retrieving sugar articles: {e}")
        return []

def display_articles(articles):
    """Display the retrieved articles in a readable format"""
    if not articles:
        print("No articles to display.")
        return
    
    print("\n" + "="*80)
    print("SUGAR NEWS ARTICLES")
    print("="*80)
    
    for i, article in enumerate(articles, 1):
        print(f"\nArticle {i}:")
        print(f"  Title: {article['title']}")
        print(f"  Source: {article['source']}")
        print(f"  Datetime: {article['datetime']}")
        print(f"  Asset: {article['asset']}")
        print(f"  Text Snippet: {article['text_snippet']}")
        print("-" * 80)

def save_to_csv(articles):
    """Save articles to a CSV file"""
    if not articles:
        print("No articles to save.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(articles)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sugar_news_articles_{timestamp}.csv"
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"\nArticles saved to: {filename}")

def main():
    """Main function"""
    print("=== SUGAR NEWS RETRIEVAL SCRIPT ===")
    print(f"Started at: {datetime.now()}")
    
    # Retrieve articles
    articles = retrieve_sugar_articles()
    
    # Display articles
    display_articles(articles)
    
    # Save to CSV
    save_to_csv(articles)
    
    print("\nScript completed.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script to test the articles retrieved from the database to verify if they are actually about sugar.
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
        LIMIT 20
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
                'text': text,
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

def test_articles_with_triage_filter(articles):
    """Test each article using the SugarTriageFilter class"""
    from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
    
    if not articles:
        print("No articles to test.")
        return []
    
    print("\nTesting articles with SugarTriageFilter...")
    
    results = []
    sugar_count = 0
    
    for article in articles:
        # Apply triage filter to the article text
        filter_result = triage_filter(article['text'])
        
        # Store the result
        result = {
            'id': article['id'],
            'title': article['title'],
            'source': article['source'],
            'datetime': article['datetime'],
            'is_about_sugar': filter_result['passed'],
            'reason': filter_result['reason'],
            'matched_zones': filter_result['matched_zones'],
            'matched_keywords': filter_result['matched_keywords'],
            'extracted_sugar_pricing': filter_result['extracted_sugar_pricing'],
            'text_snippet': article['text_snippet']
        }
        
        results.append(result)
        
        if filter_result['passed']:
            sugar_count += 1
    
    print(f"Testing completed. {sugar_count} out of {len(articles)} articles are about sugar.")
    return results

def display_test_results(results):
    """Display the test results in a readable format"""
    if not results:
        print("No results to display.")
        return
    
    print("\n" + "="*80)
    print("SUGAR ARTICLE TEST RESULTS")
    print("="*80)
    
    sugar_count = sum(1 for r in results if r['is_about_sugar'])
    print(f"\nSummary: {sugar_count} out of {len(results)} articles are about sugar ({sugar_count/len(results)*100:.1f}%)")
    
    for i, result in enumerate(results, 1):
        print(f"\nArticle {i}:")
        print(f"  Title: {result['title']}")
        print(f"  Source: {result['source']}")
        print(f"  Datetime: {result['datetime']}")
        print(f"  About Sugar: {result['is_about_sugar']}")
        print(f"  Reason: {result['reason']}")
        
        if result['matched_zones']:
            print(f"  Matched Zones: {', '.join(result['matched_zones'])}")
        
        if result['matched_keywords']:
            print(f"  Matched Keywords: {', '.join(result['matched_keywords'])}")
        
        if result['extracted_sugar_pricing']:
            print(f"  Extracted Sugar Pricing: {result['extracted_sugar_pricing']}")
        
        print(f"  Text Snippet: {result['text_snippet']}")
        print("-" * 80)

def save_results_to_json(results):
    """Save test results to a JSON file"""
    if not results:
        print("No results to save.")
        return
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sugar_article_test_results_{timestamp}.json"
    
    # Save to JSON
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nTest results saved to: {filename}")

def save_results_to_csv(results):
    """Save test results to a CSV file"""
    if not results:
        print("No results to save.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sugar_article_test_results_{timestamp}.csv"
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"\nTest results saved to: {filename}")

def main():
    """Main function"""
    print("=== SUGAR ARTICLE TESTING SCRIPT ===")
    print(f"Started at: {datetime.now()}")
    
    # Retrieve articles
    articles = retrieve_sugar_articles()
    
    if not articles:
        print("No articles retrieved. Exiting.")
        return
    
    # Test articles with triage filter
    test_results = test_articles_with_triage_filter(articles)
    
    # Display results
    display_test_results(test_results)
    
    # Save results
    save_results_to_json(test_results)
    save_results_to_csv(test_results)
    
    print("\nScript completed.")

if __name__ == "__main__":
    main()
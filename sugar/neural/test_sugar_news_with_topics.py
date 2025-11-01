#!/usr/bin/env python
"""
Test script for analyzing Sugar news articles with topics using the enhanced predictor.
Retrieves news.news articles where asset field is "Sugar", extracts topics from metadata field,
and uses the updated predictor to analyze sentiment with the topics parameter.
Saves results to the news.prompts table in ClickHouse.
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add the current directory to the path to import predictor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import CommoditySentimentPredictor


def connect_to_clickhouse():
    """
    Connect to ClickHouse database.
    
    Returns:
        Tuple of (success: bool, client: object or None, error: str or None)
    """
    try:
        from clickhouse_driver import Client
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        
        print(f"Connecting to ClickHouse at {CLICKHOUSE_NATIVE_CONFIG['host']}:{CLICKHOUSE_NATIVE_CONFIG['port']}...")
        
        # Test connection
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        
        # Execute a simple query to test connectivity
        result = client.execute('SELECT 1 as test')
        
        if result and result[0][0] == 1:
            print("✓ ClickHouse connection successful")
            return True, client, None
        else:
            print("✗ ClickHouse connection failed - unexpected result")
            return False, None, "Unexpected query result"
            
    except Exception as e:
        print(f"✗ ClickHouse connection failed: {e}")
        return False, None, str(e)


def get_sugar_news_articles(client, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve Sugar news articles from ClickHouse.
    
    Args:
        client: ClickHouse client
        limit: Maximum number of articles to retrieve
        
    Returns:
        List of article dictionaries
    """
    try:
        print(f"Retrieving up to {limit} Sugar news articles...")
        
        query = f"""
        SELECT id, datetime, source, title, text, metadata, asset, created_at
        FROM news.news
        WHERE asset = 'Sugar'
        ORDER BY datetime DESC
        LIMIT {limit}
        """
        
        result = client.execute(query)
        
        articles = []
        for row in result:
            article = {
                'id': row[0],
                'datetime': row[1],
                'source': row[2],
                'title': row[3],
                'text': row[4],
                'metadata': row[5],
                'asset': row[6],
                'created_at': row[7]
            }
            articles.append(article)
        
        print(f"✓ Retrieved {len(articles)} Sugar news articles")
        return articles
        
    except Exception as e:
        print(f"✗ Error retrieving Sugar news articles: {e}")
        return []


def extract_topics_from_metadata(metadata_str: str) -> Optional[List[str]]:
    """
    Extract topics from metadata field.
    
    Args:
        metadata_str: JSON string containing metadata
        
    Returns:
        List of topics or None if not found
    """
    try:
        if not metadata_str:
            return None
            
        metadata = json.loads(metadata_str)
        
        # Try to extract topics from various possible fields
        topics = None
        
        if 'topics' in metadata:
            topics = metadata['topics']
        elif 'keywords' in metadata:
            topics = metadata['keywords']
        elif 'tags' in metadata:
            topics = metadata['tags']
        elif 'categories' in metadata:
            topics = metadata['categories']
        
        # Ensure topics is a list of strings
        if topics is not None:
            if isinstance(topics, str):
                topics = [topics]
            elif isinstance(topics, list):
                topics = [str(topic) for topic in topics if topic]
            else:
                topics = None
        
        return topics
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not parse metadata: {e}")
        return None


def analyze_articles_with_predictor(articles: List[Dict[str, Any]], predictor: CommoditySentimentPredictor) -> List[Dict[str, Any]]:
    """
    Analyze articles using the enhanced predictor with topics.
    
    Args:
        articles: List of article dictionaries
        predictor: Enhanced CommoditySentimentPredictor instance
        
    Returns:
        List of analysis results
    """
    print(f"Analyzing {len(articles)} articles with enhanced predictor...")
    
    results = []
    
    for i, article in enumerate(articles):
        print(f"\n--- Article {i+1}/{len(articles)} ---")
        print(f"Title: {article['title'][:100]}...")
        print(f"ID: {article['id']}")
        
        # Extract topics from metadata
        topics = extract_topics_from_metadata(article['metadata'])
        print(f"Topics: {topics}")
        
        try:
            # Analyze sentiment with topics and datetime
            result = predictor.analyze_sentiment(
                text=article['text'],
                title=article['title'],
                commodity=article['asset'],
                topics=topics,
                article_id=article['id'],
                datetime=article['datetime']
            )
            
            # Combine article info with analysis result
            analysis_result = {
                'article_id': article['id'],
                'title': article['title'],
                'source': article['source'],
                'datetime': article['datetime'],
                'asset': article['asset'],
                'topics': topics,
                'sentiment': result['sentiment'],
                'confidence': result['confidence'],
                'reasoning': result['reasoning']
            }
            
            results.append(analysis_result)
            
            print(f"✓ Analysis completed - Sentiment: {result['sentiment']}, Confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            print(f"✗ Error analyzing article: {e}")
            
            # Add error result
            error_result = {
                'article_id': article['id'],
                'title': article['title'],
                'source': article['source'],
                'datetime': article['datetime'],
                'asset': article['asset'],
                'topics': topics,
                'sentiment': 'neutral',
                'confidence': 0.0,
                'reasoning': f'Error processing article: {str(e)}',
                'error': str(e)
            }
            
            results.append(error_result)
    
    return results


def save_analysis_results(results: List[Dict[str, Any]], output_file: Optional[str] = None) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        results: List of analysis results
        output_file: Optional output file path
    """
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"sugar_news_analysis_results_{timestamp}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ Analysis results saved to: {output_file}")
        
    except Exception as e:
        print(f"✗ Error saving analysis results: {e}")


def print_summary(results: List[Dict[str, Any]]) -> None:
    """
    Print a summary of the analysis results.
    
    Args:
        results: List of analysis results
    """
    if not results:
        print("No results to summarize.")
        return
    
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Total articles analyzed: {len(results)}")
    
    # Count sentiments
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    error_count = 0
    
    for result in results:
        if 'error' in result:
            error_count += 1
        else:
            sentiment = result['sentiment']
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
    
    print(f"Sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        percentage = (count / (len(results) - error_count)) * 100 if (len(results) - error_count) > 0 else 0
        print(f"  {sentiment.capitalize()}: {count} ({percentage:.1f}%)")
    
    if error_count > 0:
        print(f"Errors: {error_count}")
    
    # Average confidence
    valid_results = [r for r in results if 'error' not in r]
    if valid_results:
        avg_confidence = sum(r['confidence'] for r in valid_results) / len(valid_results)
        print(f"Average confidence: {avg_confidence:.2f}")
    
    # Topics distribution
    all_topics = []
    for result in results:
        topics = result.get('topics')
        if topics:
            all_topics.extend(topics)
    
    if all_topics:
        from collections import Counter
        topic_counts = Counter(all_topics)
        print(f"\nTop topics:")
        for topic, count in topic_counts.most_common(10):
            print(f"  {topic}: {count}")


def main():
    """
    Main function to run the test.
    """
    print("=== Sugar News Analysis with Topics Test ===\n")
    
    # Check if API key is available
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        print("❌ NEBIUS_API_KEY not found in environment variables")
        return 1
    
    print("✓ API key found")
    
    # Connect to ClickHouse
    conn_success, client, conn_error = connect_to_clickhouse()
    if not conn_success:
        print(f"❌ Failed to connect to ClickHouse: {conn_error}")
        return 1
    
    try:
        # Get Sugar news articles
        articles = get_sugar_news_articles(client, limit=5)
        if not articles:
            print("❌ No Sugar news articles found")
            return 1
        
        # Initialize predictor with prompt saving enabled
        try:
            predictor = CommoditySentimentPredictor(api_key=api_key, save_prompts=True)
            print("✓ Predictor initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing predictor: {e}")
            return 1
        
        # Analyze articles
        results = analyze_articles_with_predictor(articles, predictor)
        
        # Save results
        save_analysis_results(results)
        
        # Print summary
        print_summary(results)
        
        print("\n✅ Test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Unexpected error during test: {e}")
        return 1
    
    finally:
        # Close ClickHouse connection
        try:
            client.disconnect()
            print("✓ ClickHouse connection closed")
        except:
            pass


if __name__ == "__main__":
    exit(main())
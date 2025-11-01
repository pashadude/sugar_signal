#!/usr/bin/env python
"""
Test script to analyze sentiment of 10 random sugar articles from the database
using the CommoditySentimentPredictor with datetime and topics parameters.
"""

import sys
import os
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the current directory to the path to import predictor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import CommoditySentimentPredictor

# Add the backend config path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from config import CLICKHOUSE_NATIVE_CONFIG

def connect_to_clickhouse():
    """
    Connect to ClickHouse database.
    
    Returns:
        Tuple of (success: bool, client: object or None, error: str or None)
    """
    try:
        from clickhouse_driver import Client
        
        print("Connecting to ClickHouse...")
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        
        # Test connection
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

def get_random_sugar_articles(client, count: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve random sugar articles from the database.
    
    Args:
        client: ClickHouse client
        count: Number of articles to retrieve
        
    Returns:
        List of article dictionaries
    """
    try:
        print(f"Retrieving {count} random sugar articles...")
        
        # Query to get random sugar articles
        query = f"""
        SELECT id, datetime, source, title, text, metadata, asset
        FROM news.news 
        WHERE asset = 'Sugar' 
        AND text != '' 
        AND title != ''
        ORDER BY rand() 
        LIMIT {count}
        """
        
        articles = client.execute(query)
        
        if not articles:
            print("✗ No sugar articles found in the database")
            return []
        
        print(f"✓ Retrieved {len(articles)} sugar articles")
        
        # Convert to list of dictionaries
        article_dicts = []
        for article in articles:
            article_dict = {
                'id': article[0],
                'datetime': article[1],
                'source': article[2],
                'title': article[3],
                'text': article[4],
                'metadata': article[5],
                'asset': article[6]
            }
            article_dicts.append(article_dict)
        
        return article_dicts
        
    except Exception as e:
        print(f"✗ Error retrieving articles: {e}")
        return []

def extract_topics_from_metadata(metadata_str: str) -> List[str]:
    """
    Extract topics from metadata JSON string.
    
    Args:
        metadata_str: JSON string containing metadata
        
    Returns:
        List of topics
    """
    try:
        if not metadata_str:
            return []
        
        metadata = json.loads(metadata_str)
        
        # Try to extract topics from various possible fields
        topics = []
        
        if 'topics' in metadata and isinstance(metadata['topics'], list):
            topics.extend(metadata['topics'])
        
        if 'keywords' in metadata and isinstance(metadata['keywords'], list):
            topics.extend(metadata['keywords'])
        
        if 'tags' in metadata and isinstance(metadata['tags'], list):
            topics.extend(metadata['tags'])
        
        # Remove duplicates and limit to reasonable number
        unique_topics = list(set(topics))[:10]  # Limit to 10 topics
        
        return unique_topics
        
    except (json.JSONDecodeError, Exception):
        return []

def analyze_articles_with_predictor(articles: List[Dict[str, Any]], predictor: CommoditySentimentPredictor) -> List[Dict[str, Any]]:
    """
    Analyze articles using the sentiment predictor.
    
    Args:
        articles: List of article dictionaries
        predictor: CommoditySentimentPredictor instance
        
    Returns:
        List of analysis results
    """
    print("Analyzing articles with sentiment predictor...")
    
    results = []
    
    for i, article in enumerate(articles, 1):
        print(f"\n--- Analyzing article {i}/{len(articles)} ---")
        print(f"Title: {article['title'][:80]}...")
        print(f"Datetime: {article['datetime']}")
        
        try:
            # Extract topics from metadata
            topics = extract_topics_from_metadata(article['metadata'])
            
            # Parse datetime
            datetime_obj = article['datetime']
            if isinstance(datetime_obj, str):
                try:
                    datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
                except ValueError:
                    datetime_obj = None
            
            # Analyze sentiment
            result = predictor.analyze_sentiment(
                text=article['text'],
                title=article['title'],
                commodity=article['asset'],
                topics=topics if topics else None,
                article_id=article['id'],
                datetime=datetime_obj
            )
            
            # Debug: Print the raw result
            print(f"Raw result: {result}")
            
            # Extract sentiment, confidence, and reasoning from the result
            sentiment = result['sentiment']
            confidence = result['confidence']
            reasoning = result['reasoning']
            
            # The predictor already parses the JSON response, so we don't need to parse it again
            # However, if the reasoning contains JSON artifacts, clean them up
            if reasoning.startswith('') and '{' in reasoning:
                try:
                    # Extract just the reasoning part without JSON artifacts
                    lines = reasoning.split('\n')
                    clean_lines = []
                    skip_next = False
                    for line in lines:
                        if line.strip().startswith('{') or line.strip().startswith('"sentiment"'):
                            skip_next = True
                        elif line.strip().startswith('}') or line.strip().startswith('"reasoning"'):
                            skip_next = False
                            continue
                        elif not skip_next and line.strip() and not line.strip().startswith('\"'):
                            clean_lines.append(line)
                    
                    if clean_lines:
                        reasoning = '\n'.join(clean_lines).strip()
                except Exception as e:
                    print(f"Error cleaning reasoning: {e}")
                    pass
            
            # If reasoning is empty or contains only placeholder text, use a default message
            if not reasoning or reasoning.strip() in ['', '', '\n']:
                reasoning = "No detailed reasoning provided by the model."
            
            # Combine article info with analysis result
            analysis_result = {
                'article_id': article['id'],
                'title': article['title'],
                'datetime': article['datetime'].isoformat() if hasattr(article['datetime'], 'isoformat') else str(article['datetime']),
                'source': article['source'],
                'topics': topics,
                'sentiment': sentiment,
                'confidence': confidence,
                'reasoning': reasoning
            }
            
            results.append(analysis_result)
            
            print(f"✓ Analysis completed")
            print(f"  Sentiment: {result['sentiment'].upper()}")
            print(f"  Confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            print(f"✗ Error analyzing article: {e}")
            
            # Add error result
            error_result = {
                'article_id': article['id'],
                'title': article['title'],
                'datetime': article['datetime'].isoformat() if hasattr(article['datetime'], 'isoformat') else str(article['datetime']),
                'source': article['source'],
                'topics': extract_topics_from_metadata(article['metadata']),
                'sentiment': 'error',
                'confidence': 0.0,
                'reasoning': f'Error during analysis: {str(e)}',
                'error': str(e)
            }
            
            results.append(error_result)
    
    return results

def display_results(results: List[Dict[str, Any]]):
    """
    Display analysis results in a readable format.
    
    Args:
        results: List of analysis results
    """
    print("\n" + "="*80)
    print("SENTIMENT ANALYSIS RESULTS")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Article {i} ---")
        print(f"Title: {result['title']}")
        print(f"Datetime: {result['datetime']}")
        print(f"Source: {result['source']}")
        
        if result['topics']:
            print(f"Topics: {', '.join(result['topics'])}")
        
        if 'error' in result:
            print(f"Status: ERROR - {result['error']}")
        else:
            print(f"Sentiment: {result['sentiment'].upper()}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Reasoning: {result['reasoning']}")

def calculate_summary_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from the analysis results.
    
    Args:
        results: List of analysis results
        
    Returns:
        Dictionary with summary statistics
    """
    stats = {
        'total_articles': len(results),
        'successful_analyses': 0,
        'failed_analyses': 0,
        'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0, 'error': 0},
        'confidence_scores': [],
        'average_confidence': 0.0
    }
    
    for result in results:
        if 'error' in result:
            stats['failed_analyses'] += 1
            stats['sentiment_distribution']['error'] += 1
        else:
            stats['successful_analyses'] += 1
            sentiment = result['sentiment']
            if sentiment in stats['sentiment_distribution']:
                stats['sentiment_distribution'][sentiment] += 1
            
            confidence = result['confidence']
            stats['confidence_scores'].append(confidence)
    
    # Calculate average confidence
    if stats['confidence_scores']:
        stats['average_confidence'] = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
    
    return stats

def display_summary_statistics(stats: Dict[str, Any]):
    """
    Display summary statistics.
    
    Args:
        stats: Summary statistics dictionary
    """
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print(f"Total articles analyzed: {stats['total_articles']}")
    print(f"Successful analyses: {stats['successful_analyses']}")
    print(f"Failed analyses: {stats['failed_analyses']}")
    
    print("\nSentiment Distribution:")
    for sentiment, count in stats['sentiment_distribution'].items():
        percentage = (count / stats['total_articles']) * 100 if stats['total_articles'] > 0 else 0
        print(f"  {sentiment.upper()}: {count} ({percentage:.1f}%)")
    
    if stats['confidence_scores']:
        print(f"\nAverage confidence: {stats['average_confidence']:.2f}")
        print(f"Min confidence: {min(stats['confidence_scores']):.2f}")
        print(f"Max confidence: {max(stats['confidence_scores']):.2f}")

def save_results_to_json(results: List[Dict[str, Any]], stats: Dict[str, Any], filename: str = None):
    """
    Save results and statistics to a JSON file.
    
    Args:
        results: List of analysis results
        stats: Summary statistics
        filename: Output filename (optional)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sugar_sentiment_analysis_{timestamp}.json"
    
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(results),
            'model': 'Qwen/Qwen3-32B-LoRa:my-custom-model-commodity-pedw'
        },
        'summary_statistics': stats,
        'results': results
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Results saved to: {filename}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error saving results to file: {e}")
        return False

def main():
    """
    Main function to run the sentiment analysis test.
    """
    print("=== SUGAR SENTIMENT ANALYSIS TEST ===")
    print(f"Started at: {datetime.now()}")
    
    # Step 1: Connect to ClickHouse
    conn_success, client, conn_error = connect_to_clickhouse()
    if not conn_success:
        print(f"Cannot continue - database connection failed: {conn_error}")
        return 1
    
    # Step 2: Get random sugar articles
    articles = get_random_sugar_articles(client, count=10)
    if not articles:
        print("Cannot continue - no articles retrieved from database")
        client.disconnect()
        return 1
    
    # Close database connection
    try:
        client.disconnect()
        print("✓ Database connection closed")
    except:
        pass
    
    # Step 3: Initialize predictor
    try:
        print("\nInitializing sentiment predictor...")
        predictor = CommoditySentimentPredictor()
        print("✓ Predictor initialized successfully")
    except ValueError as e:
        print(f"✗ Error initializing predictor: {e}")
        return 1
    
    # Step 4: Analyze articles
    results = analyze_articles_with_predictor(articles, predictor)
    
    # Step 5: Display results
    display_results(results)
    
    # Step 6: Calculate and display summary statistics
    stats = calculate_summary_statistics(results)
    display_summary_statistics(stats)
    
    # Step 7: Save results to JSON file
    save_results_to_json(results, stats)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    exit(main())
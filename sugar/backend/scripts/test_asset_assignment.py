#!/usr/bin/env python
"""
Test script to verify that the sugar news pipeline correctly assigns asset values
based on the triage filter result.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import normalize_and_filter_article
from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline

def create_test_articles():
    """Create test articles with varying relevance to sugar"""
    return [
        {
            'title': 'Brazil Sugar Exports Rise on Strong Demand',
            'text': 'Brazilian sugar exports increased by 15% this month due to strong international demand for raw sugar. The Center-South region reported record production levels.',
            'site_name': 'Commodity News',
            'published_date': '2024-01-15',
            'url': 'https://example.com/brazil-sugar-exports',
            'score': 0.85
        },
        {
            'title': 'Oil Prices Surge Amid Middle East Tensions',
            'text': 'Crude oil prices surged to $90 per barrel as tensions in the Middle East escalated. Energy markets are volatile.',
            'site_name': 'Energy Daily',
            'published_date': '2024-01-16',
            'url': 'https://example.com/oil-prices-surge',
            'score': 0.82
        },
        {
            'title': 'Sugar Futures Hit 6-Month High',
            'text': 'Sugar futures on the NY11 exchange reached a 6-month high as concerns about weather impact on Brazilian crops grow. Traders are closely watching the market.',
            'site_name': 'Market Watch',
            'published_date': '2024-01-17',
            'url': 'https://example.com/sugar-futures-high',
            'score': 0.88
        },
        {
            'title': 'Gold Prices Stable as Investors Wait for Fed Decision',
            'text': 'Gold prices remained stable as investors await the Federal Reserve decision on interest rates. The precious metal market is in a holding pattern.',
            'site_name': 'Financial Times',
            'published_date': '2024-01-18',
            'url': 'https://example.com/gold-prices-stable',
            'score': 0.79
        },
        {
            'title': 'India Sugar Production Forecast Cut Due to Drought',
            'text': 'India has cut its sugar production forecast by 8% due to drought conditions in key growing regions. This could impact global sugar supply.',
            'site_name': 'Agriculture Today',
            'published_date': '2024-01-19',
            'url': 'https://example.com/india-sugar-production',
            'score': 0.86
        }
    ]

def test_asset_assignment():
    """Test that articles are correctly assigned asset values based on triage filter"""
    print("=== Testing Asset Assignment Logic ===\n")
    
    # Create test articles
    test_articles = create_test_articles()
    
    # Initialize normalization pipeline
    normalization_pipeline = LanguageNormalizationPipeline()
    
    # Process each article
    results = []
    for i, article in enumerate(test_articles, 1):
        print(f"Processing Article {i}: {article['title']}")
        
        # Apply normalization and triage filter
        result = normalize_and_filter_article(article, normalization_pipeline)
        
        if result:
            asset = result.get('asset', 'Unknown')
            triage_passed = result.get('triage_passed', False)
            triage_reason = result.get('triage_reason', 'No reason provided')
            
            print(f"  Asset: {asset}")
            print(f"  Triage Passed: {triage_passed}")
            print(f"  Triage Reason: {triage_reason}")
            print(f"  Matched Zones: {result.get('matched_zones', [])}")
            print(f"  Matched Keywords: {result.get('matched_keywords', [])}")
            print()
            
            results.append({
                'title': article['title'],
                'asset': asset,
                'triage_passed': triage_passed,
                'triage_reason': triage_reason
            })
        else:
            print("  Article was rejected (no result returned)")
            print()
    
    # Analyze results
    print("=== Results Analysis ===")
    df_results = pd.DataFrame(results)
    
    sugar_articles = df_results[df_results['asset'] == 'Sugar']
    general_articles = df_results[df_results['asset'] == 'General']
    
    print(f"\nTotal articles processed: {len(df_results)}")
    print(f"Sugar articles (passed triage): {len(sugar_articles)}")
    print(f"General articles (failed triage): {len(general_articles)}")
    
    print("\nSugar Articles:")
    for _, row in sugar_articles.iterrows():
        print(f"  - {row['title']}")
        print(f"    Reason: {row['triage_reason']}")
    
    print("\nGeneral Articles:")
    for _, row in general_articles.iterrows():
        print(f"  - {row['title']}")
        print(f"    Reason: {row['triage_reason']}")
    
    # Verify expectations
    expected_sugar_count = 3  # Brazil sugar exports, sugar futures, India sugar production
    expected_general_count = 2  # Oil prices, gold prices
    
    actual_sugar_count = len(sugar_articles)
    actual_general_count = len(general_articles)
    
    print("\n=== Verification ===")
    if actual_sugar_count == expected_sugar_count:
        print(f"✓ Correct number of sugar articles: {actual_sugar_count}")
    else:
        print(f"✗ Incorrect number of sugar articles: expected {expected_sugar_count}, got {actual_sugar_count}")
    
    if actual_general_count == expected_general_count:
        print(f"✓ Correct number of general articles: {actual_general_count}")
    else:
        print(f"✗ Incorrect number of general articles: expected {expected_general_count}, got {actual_general_count}")
    
    # Check that all sugar articles passed triage
    sugar_triage_passed = sugar_articles['triage_passed'].all()
    if sugar_triage_passed:
        print("✓ All sugar articles passed triage filter")
    else:
        print("✗ Some sugar articles failed triage filter")
    
    # Check that all general articles failed triage
    general_triage_failed = not general_articles['triage_passed'].any()
    if general_triage_failed:
        print("✓ All general articles failed triage filter")
    else:
        print("✗ Some general articles passed triage filter")
    
    return df_results

if __name__ == "__main__":
    try:
        results_df = test_asset_assignment()
        print("\n=== Test Completed ===")
    except Exception as e:
        print(f"Error during testing: {e}")
        sys.exit(1)
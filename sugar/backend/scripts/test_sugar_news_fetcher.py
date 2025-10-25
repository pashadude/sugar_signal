#!/usr/bin/env python3
"""
Test script to verify the modified sugar news fetcher implementation.

This script tests:
1. That sugar sources undergo the same filtering as other sources
2. That sugar sources are still being queried and processed
3. That the combined results include articles from both sugar and non-sugar sources
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

# Import the modules we need to test
from sugar.backend.parsers.sugar_news_fetcher import (
    fetch_sugar_articles_for_period,
    SUGAR_SOURCES,
    ALL_SUGAR_SOURCE_NAMES,
    SUGAR_CONFIG
)
from sugar.backend.parsers.source_filter import get_sugar_trusted_sources, get_non_trusted_sources
from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline

def create_mock_article(title, text, site_name, is_sugar_source=True):
    """Create a mock article for testing"""
    return {
        'title': title,
        'text': text,
        'site_name': site_name,
        'url': f'https://{site_name}/article/{hash(title) % 1000}',
        'published_date': datetime.now().strftime('%Y-%m-%d'),
        'score': 0.8
    }

def create_mock_api_response(articles):
    """Create a mock API response DataFrame"""
    return pd.DataFrame(articles)

def test_sugar_sources_filtering():
    """Test that sugar sources undergo the same filtering as other sources"""
    print("\n=== TEST 1: Sugar Sources Filtering ===")
    
    # Create mock articles from sugar and non-sugar sources
    sugar_source_articles = [
        create_mock_article(
            "Sugar prices rise in Brazil",
            "Sugar prices in Brazil have risen due to increased demand.",
            "sugarproducer.com",  # This is a sugar source
            is_sugar_source=True
        ),
        create_mock_article(
            "Sugar beet harvest in Europe",
            "The sugar beet harvest in Europe is expected to be lower this year.",
            "argusmedia.com",  # This is a sugar source
            is_sugar_source=True
        ),
        create_mock_article(
            "Non-sugar article from sugar source",
            "This article is about copper mining and has nothing to do with sugar.",
            "foodprocessing.com",  # This is a sugar source but article is not about sugar
            is_sugar_source=True
        )
    ]
    
    non_sugar_source_articles = [
        create_mock_article(
            "Global sugar market analysis",
            "The global sugar market is experiencing volatility due to weather conditions.",
            "reuters.com",  # This is not a sugar source
            is_sugar_source=False
        ),
        create_mock_article(
            "Sugar futures trading",
            "Sugar futures are trading higher on the commodities market.",
            "bloomberg.com",  # This is not a sugar source
            is_sugar_source=False
        ),
        create_mock_article(
            "Non-sugar article from non-sugar source",
            "This article is about oil prices and has nothing to do with sugar.",
            "cnn.com",  # This is not a sugar source and article is not about sugar
            is_sugar_source=False
        )
    ]
    
    # Create mock API responses
    sugar_response = create_mock_api_response(sugar_source_articles)
    non_sugar_response = create_mock_api_response(non_sugar_source_articles)
    
    # Mock the OpointAPI
    with patch('sugar.backend.parsers.sugar_news_fetcher.OpointAPI') as mock_api_class:
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # Configure the mock to return our test data
        def mock_search_articles(*args, **kwargs):
            if 'site_id' in kwargs:
                # This is a sugar source query
                return sugar_response
            else:
                # This is a non-sugar source query
                return non_sugar_response
        
        def mock_search_site_and_articles(*args, **kwargs):
            return sugar_response
        
        mock_api.search_articles.side_effect = mock_search_articles
        mock_api.search_site_and_articles.side_effect = mock_search_site_and_articles
        
        # Create a normalization pipeline
        normalization_pipeline = Mock()
        normalization_pipeline.normalize = Mock(side_effect=lambda x: x)  # Simple pass-through
        
        # Call the function under test
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result_df = fetch_sugar_articles_for_period(
            api_key="test_key",
            start_date=start_date,
            end_date=end_date,
            topic_ids=['20000373'],
            max_articles=100,
            normalization_pipeline=normalization_pipeline
        )
        
        # Verify the results
        if result_df.empty:
            print("❌ FAIL: No articles returned")
            return False
        
        # Check that we have articles from both sugar and non-sugar sources
        sugar_source_results = result_df[result_df['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)]
        non_sugar_source_results = result_df[~result_df['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)]
        
        if len(sugar_source_results) == 0:
            print("❌ FAIL: No articles from sugar sources")
            return False
        
        if len(non_sugar_source_results) == 0:
            print("❌ FAIL: No articles from non-sugar sources")
            return False
        
        # Check that sugar sources were filtered (non-sugar articles from sugar sources should be filtered out)
        sugar_source_non_sugar_articles = sugar_source_results[sugar_source_results['asset'] == 'General']
        if len(sugar_source_non_sugar_articles) > 0:
            print(f"⚠️  WARNING: Found {len(sugar_source_non_sugar_articles)} non-sugar articles from sugar sources that passed filtering")
        
        # Check that non-sugar sources were filtered (non-sugar articles from non-sugar sources should be filtered out)
        non_sugar_source_non_sugar_articles = non_sugar_source_results[non_sugar_source_results['asset'] == 'General']
        if len(non_sugar_source_non_sugar_articles) > 0:
            print(f"⚠️  WARNING: Found {len(non_sugar_source_non_sugar_articles)} non-sugar articles from non-sugar sources that passed filtering")
        
        print(f"✅ PASS: Found {len(sugar_source_results)} articles from sugar sources and {len(non_sugar_source_results)} articles from non-sugar sources")
        print(f"   - Sugar sources with sugar articles: {len(sugar_source_results[sugar_source_results['asset'] == 'Sugar'])}")
        print(f"   - Non-sugar sources with sugar articles: {len(non_sugar_source_results[non_sugar_source_results['asset'] == 'Sugar'])}")
        
        return True

def test_sugar_sources_queried_separately():
    """Test that sugar sources are queried separately from other sources"""
    print("\n=== TEST 2: Separate Querying of Sugar Sources ===")
    
    # Mock the OpointAPI
    with patch('sugar.backend.parsers.sugar_news_fetcher.OpointAPI') as mock_api_class:
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # Track calls to the API
        sugar_source_calls = []
        non_sugar_source_calls = []
        
        def mock_search_articles(*args, **kwargs):
            if 'site_id' in kwargs:
                # This is a sugar source query
                sugar_source_calls.append(kwargs)
                # Return empty DataFrame for simplicity
                return pd.DataFrame()
            else:
                # This is a non-sugar source query
                non_sugar_source_calls.append(kwargs)
                # Return empty DataFrame for simplicity
                return pd.DataFrame()
        
        def mock_search_site_and_articles(*args, **kwargs):
            sugar_source_calls.append(kwargs)
            return pd.DataFrame()
        
        mock_api.search_articles.side_effect = mock_search_articles
        mock_api.search_site_and_articles.side_effect = mock_search_site_and_articles
        
        # Create a normalization pipeline
        normalization_pipeline = Mock()
        normalization_pipeline.normalize = Mock(side_effect=lambda x: x)
        
        # Call the function under test
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        fetch_sugar_articles_for_period(
            api_key="test_key",
            start_date=start_date,
            end_date=end_date,
            topic_ids=['20000373'],
            max_articles=100,
            normalization_pipeline=normalization_pipeline
        )
        
        # Verify that sugar sources were queried separately
        if len(sugar_source_calls) == 0:
            print("❌ FAIL: No calls made to sugar sources")
            return False
        
        if len(non_sugar_source_calls) == 0:
            print("❌ FAIL: No calls made to non-sugar sources")
            return False
        
        # Check that sugar sources were queried individually
        sugar_source_ids = set()
        for call in sugar_source_calls:
            if 'site_id' in call:
                sugar_source_ids.add(call['site_id'])
        
        expected_sugar_source_ids = set(str(source['id']) for category in SUGAR_SOURCES.values() for source in category if source.get('id'))
        
        if not expected_sugar_source_ids.issubset(sugar_source_ids):
            missing_ids = expected_sugar_source_ids - sugar_source_ids
            print(f"❌ FAIL: Not all sugar sources were queried. Missing: {missing_ids}")
            return False
        
        print(f"✅ PASS: Made {len(sugar_source_calls)} calls to sugar sources and {len(non_sugar_source_calls)} calls to non-sugar sources")
        print(f"   - Queried {len(sugar_source_ids)} unique sugar source IDs")
        
        return True

def test_combined_results():
    """Test that the combined results include articles from both sugar and non-sugar sources"""
    print("\n=== TEST 3: Combined Results ===")
    
    # Create mock articles
    sugar_source_articles = [
        create_mock_article(
            "Sugar production in Brazil",
            "Brazil's sugar production is expected to increase this year.",
            "sugarproducer.com",
            is_sugar_source=True
        )
    ]
    
    non_sugar_source_articles = [
        create_mock_article(
            "Sugar prices on the rise",
            "Sugar prices are rising globally due to supply constraints.",
            "reuters.com",
            is_sugar_source=False
        )
    ]
    
    # Create mock API responses
    sugar_response = create_mock_api_response(sugar_source_articles)
    non_sugar_response = create_mock_api_response(non_sugar_source_articles)
    
    # Mock the OpointAPI
    with patch('sugar.backend.parsers.sugar_news_fetcher.OpointAPI') as mock_api_class:
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # Configure the mock to return our test data
        def mock_search_articles(*args, **kwargs):
            if 'site_id' in kwargs:
                # This is a sugar source query
                return sugar_response
            else:
                # This is a non-sugar source query
                return non_sugar_response
        
        def mock_search_site_and_articles(*args, **kwargs):
            return sugar_response
        
        mock_api.search_articles.side_effect = mock_search_articles
        mock_api.search_site_and_articles.side_effect = mock_search_site_and_articles
        
        # Create a normalization pipeline
        normalization_pipeline = Mock()
        normalization_pipeline.normalize = Mock(side_effect=lambda x: x)
        
        # Call the function under test
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result_df = fetch_sugar_articles_for_period(
            api_key="test_key",
            start_date=start_date,
            end_date=end_date,
            topic_ids=['20000373'],
            max_articles=100,
            normalization_pipeline=normalization_pipeline
        )
        
        # Verify the results
        if result_df.empty:
            print("❌ FAIL: No articles returned")
            return False
        
        # Check that we have articles from both sugar and non-sugar sources
        sugar_source_results = result_df[result_df['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)]
        non_sugar_source_results = result_df[~result_df['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)]
        
        if len(sugar_source_results) == 0:
            print("❌ FAIL: No articles from sugar sources")
            return False
        
        if len(non_sugar_source_results) == 0:
            print("❌ FAIL: No articles from non-sugar sources")
            return False
        
        # Check that all articles are about sugar (asset = 'Sugar')
        if not all(result_df['asset'] == 'Sugar'):
            non_sugar_articles = result_df[result_df['asset'] != 'Sugar']
            print(f"❌ FAIL: Found {len(non_sugar_articles)} articles not about sugar")
            return False
        
        print(f"✅ PASS: Combined results include {len(sugar_source_results)} articles from sugar sources and {len(non_sugar_source_results)} articles from non-sugar sources")
        print(f"   - All articles are correctly identified as being about sugar")
        
        return True

def test_source_filtering_applied_to_all():
    """Test that source filtering is applied to both sugar and non-sugar sources"""
    print("\n=== TEST 4: Source Filtering Applied to All Sources ===")
    
    # Get the list of non-trusted sources
    non_trusted_sources = get_non_trusted_sources()
    
    # Create mock articles from trusted and non-trusted sources
    trusted_sugar_articles = [
        create_mock_article(
            "Sugar market update",
            "The sugar market is showing signs of recovery.",
            "sugarproducer.com",  # This is a trusted sugar source
            is_sugar_source=True
        )
    ]
    
    non_trusted_sugar_articles = [
        create_mock_article(
            "Sugar news from unreliable source",
            "This article about sugar comes from a non-trusted source.",
            "Guelph Today",  # This is a non-trusted source
            is_sugar_source=True
        )
    ]
    
    trusted_non_sugar_articles = [
        create_mock_article(
            "Global sugar trade",
            "Global sugar trade is affected by recent policy changes.",
            "reuters.com",  # This is a trusted non-sugar source
            is_sugar_source=False
        )
    ]
    
    non_trusted_non_sugar_articles = [
        create_mock_article(
            "Sugar news from another unreliable source",
            "This article about sugar comes from another non-trusted source.",
            "Timminstoday",  # This is a non-trusted source
            is_sugar_source=False
        )
    ]
    
    # Create mock API responses
    sugar_response = create_mock_api_response(trusted_sugar_articles + non_trusted_sugar_articles)
    non_sugar_response = create_mock_api_response(trusted_non_sugar_articles + non_trusted_non_sugar_articles)
    
    # Mock the OpointAPI
    with patch('sugar.backend.parsers.sugar_news_fetcher.OpointAPI') as mock_api_class:
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # Configure the mock to return our test data
        def mock_search_articles(*args, **kwargs):
            if 'site_id' in kwargs:
                # This is a sugar source query
                return sugar_response
            else:
                # This is a non-sugar source query
                return non_sugar_response
        
        def mock_search_site_and_articles(*args, **kwargs):
            return sugar_response
        
        mock_api.search_articles.side_effect = mock_search_articles
        mock_api.search_site_and_articles.side_effect = mock_search_site_and_articles
        
        # Create a normalization pipeline
        normalization_pipeline = Mock()
        normalization_pipeline.normalize = Mock(side_effect=lambda x: x)
        
        # Call the function under test
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        result_df = fetch_sugar_articles_for_period(
            api_key="test_key",
            start_date=start_date,
            end_date=end_date,
            topic_ids=['20000373'],
            max_articles=100,
            normalization_pipeline=normalization_pipeline
        )
        
        # Verify the results
        if result_df.empty:
            print("❌ FAIL: No articles returned")
            return False
        
        # Check that non-trusted sources were filtered out
        non_trusted_results = result_df[result_df['site_name'].isin(non_trusted_sources)]
        
        if len(non_trusted_results) > 0:
            print(f"❌ FAIL: Found {len(non_trusted_results)} articles from non-trusted sources that should have been filtered out")
            return False
        
        # Check that we still have articles from trusted sources
        trusted_results = result_df[~result_df['site_name'].isin(non_trusted_sources)]
        
        if len(trusted_results) == 0:
            print("❌ FAIL: No articles from trusted sources")
            return False
        
        print(f"✅ PASS: Source filtering correctly applied to all sources")
        print(f"   - {len(trusted_results)} articles from trusted sources")
        print(f"   - 0 articles from non-trusted sources (correctly filtered out)")
        
        return True

def main():
    """Main function to run all tests"""
    print("=== SUGAR NEWS FETCHER TEST SUITE ===")
    print(f"Started at: {datetime.now()}")
    
    tests = [
        ("Sugar Sources Filtering", test_sugar_sources_filtering),
        ("Separate Querying of Sugar Sources", test_sugar_sources_queried_separately),
        ("Combined Results", test_combined_results),
        ("Source Filtering Applied to All", test_source_filtering_applied_to_all)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning test: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED with exception: {str(e)}")
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The sugar news fetcher implementation is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
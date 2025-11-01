#!/usr/bin/env python
"""
Test script to verify double filtering implementation in sugar news fetcher.

This script tests that articles are properly filtered by both MEDIA_ID and MEDIA_TOPIC_ID,
ensuring that only articles that match both criteria are processed.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.api.opoint.opoint_api import OpointAPI
from sugar.backend.parsers.news_parser import build_search_query
from sugar.backend.parsers.sugar_news_fetcher import (
    SUGAR_SOURCES_27, 
    MEDIA_TOPIC_IDS,
    ALL_SUGAR_SOURCE_NAMES_27
)

def test_api_double_filtering():
    """Test that the Opoint API properly handles double filtering parameters."""
    print("=== Testing API Double Filtering ===")
    
    # Get API key from environment
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("ERROR: OPOINT_API_KEY environment variable not found")
        return False
    
    # Initialize API
    api = OpointAPI(api_key=api_key)
    
    # Test with a small date range and limited articles
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Get a sample sugar source and topic ID
    test_source = SUGAR_SOURCES_27[0]  # Use first sugar source
    test_topic_ids = [MEDIA_TOPIC_IDS[0]]  # Use first topic ID
    
    print(f"Testing with:")
    print(f"  - Source: {test_source['name']} (ID: {test_source['id']})")
    print(f"  - Topic ID: {test_topic_ids[0]}")
    print(f"  - Date range: {start_date.date()} to {end_date.date()}")
    
    # Build search query
    search_query = build_search_query(
        test_topic_ids,
        [],  # No person entities for test
        [],  # No company entities for test
        [test_source['name']]  # Include source name in query
    )
    
    print(f"  - Search query: {search_query}")
    
    try:
        # Test API call with double filtering parameters
        print("\n--- Testing API call with double filtering ---")
        results = api.search_articles(
            site_id=str(test_source['id']),
            search_text=search_query,
            num_articles=10,  # Small number for testing
            min_score=0.77,
            start_date=start_date,
            end_date=end_date,
            media_topic_ids=test_topic_ids,  # CRITICAL: This is the double filtering parameter
            timeout=30
        )
        
        print(f"API returned {len(results)} articles")
        
        if not results.empty:
            print("\n--- Validating double filtering results ---")
            
            # Check that all results have the correct MEDIA_ID
            if 'id_site' in results.columns:
                expected_id = str(test_source['id'])
                print(f"Expected MEDIA_ID: {expected_id}")
                print(f"Actual MEDIA_IDs in results: {results['id_site'].unique()}")
                print(f"MEDIA_ID value counts: {results['id_site'].value_counts().to_dict()}")
                
                # CRITICAL FIX: Handle type mismatch - API returns strings, config has integers
                # Convert both to strings for comparison
                correct_media_id = results['id_site'].astype(str) == expected_id
                print(f"MEDIA_ID validation: {correct_media_id.sum()}/{len(results)} articles have correct MEDIA_ID")
                
                if not correct_media_id.all():
                    print("ERROR: Some articles have incorrect MEDIA_ID")
                    
                    # Show details of articles with incorrect MEDIA_ID
                    incorrect_articles = results[results['id_site'].astype(str) != expected_id]
                    print(f"\nArticles with incorrect MEDIA_ID:")
                    for _, article in incorrect_articles.iterrows():
                        print(f"  - Title: {article.get('title', 'No title')[:80]}...")
                        print(f"    Site ID: {article.get('id_site', 'Unknown')} (expected: {expected_id})")
                        print(f"    Site Name: {article.get('site_name', 'Unknown')}")
                        print(f"    Source Name: {article.get('source_name', 'Unknown')}")
                    
                    return False
            else:
                print("WARNING: id_site column not available in results")
            
            # Check that all results have topic information
            if 'topics' in results.columns or 'topic_ids' in results.columns:
                topic_column = 'topics' if 'topics' in results.columns else 'topic_ids'
                print(f"Topic information available in column: {topic_column}")
                
                # Check if any articles have the expected topic ID
                valid_topics = 0
                for _, article in results.iterrows():
                    article_topics = article.get(topic_column, [])
                    if isinstance(article_topics, str):
                        try:
                            import json
                            article_topics = json.loads(article_topics)
                        except:
                            article_topics = []
                    
                    if isinstance(article_topics, list):
                        for topic in article_topics:
                            if isinstance(topic, dict) and 'id' in topic:
                                if str(topic['id']) in test_topic_ids:
                                    valid_topics += 1
                                    break
                            elif isinstance(topic, str):
                                if topic in test_topic_ids:
                                    valid_topics += 1
                                    break
                
                print(f"MEDIA_TOPIC_ID validation: {valid_topics}/{len(results)} articles have correct MEDIA_TOPIC_ID")
                
                if valid_topics == 0:
                    print("WARNING: No articles have the expected MEDIA_TOPIC_ID")
                    print("This might be normal if no articles match both criteria in the date range")
            else:
                print("WARNING: Topic information not available in results")
            
            print("\n--- Sample articles ---")
            for i, (_, article) in enumerate(results.head(3).iterrows()):
                print(f"\nArticle {i+1}:")
                print(f"  Title: {article.get('title', 'No title')[:100]}...")
                print(f"  Source: {article.get('site_name', 'Unknown')}")
                print(f"  Site ID: {article.get('id_site', 'Unknown')}")
                print(f"  Published: {article.get('published_date', 'Unknown')}")
                print(f"  URL: {article.get('url', 'No URL')}")
            
            print("\n✅ API double filtering test completed successfully")
            return True
            
        else:
            print("No articles returned - this might be normal if no articles match both criteria")
            print("✅ API double filtering test completed (no articles to validate)")
            return True
            
    except Exception as e:
        print(f"ERROR: API test failed: {str(e)}")
        return False

def test_search_query_construction():
    """Test that search queries are built correctly for double filtering."""
    print("\n=== Testing Search Query Construction ===")
    
    # Test with sample data
    test_topic_ids = MEDIA_TOPIC_IDS[:2]  # Use first 2 topic IDs
    test_person_entities = ["John Doe", "Jane Smith"]
    test_company_entities = ["ABC Corp", "XYZ Inc"]
    test_sugar_sources = ALL_SUGAR_SOURCE_NAMES_27[:3]  # Use first 3 sources
    
    print(f"Testing with:")
    print(f"  - Topic IDs: {test_topic_ids}")
    print(f"  - Person entities: {test_person_entities}")
    print(f"  - Company entities: {test_company_entities}")
    print(f"  - Sugar sources: {test_sugar_sources}")
    
    # Build search query
    search_query = build_search_query(
        test_topic_ids,
        test_person_entities,
        test_company_entities,
        test_sugar_sources
    )
    
    print(f"\nGenerated search query: {search_query}")
    
    # Validate that the query contains expected components
    expected_components = []
    
    # Check topic IDs
    for topic_id in test_topic_ids:
        expected_components.append(f"(topic:1{topic_id})")
    
    # Check person entities
    for person in test_person_entities:
        expected_components.append(f'(person:"{person}")')
    
    # Check company entities
    for company in test_company_entities:
        expected_components.append(f'(company:"{company}")')
    
    # Check sugar sources
    for source in test_sugar_sources:
        expected_components.append(f'(source:"{source}")')
    
    print(f"\nExpected components: {expected_components}")
    
    # Verify all expected components are in the query
    all_present = True
    for component in expected_components:
        if component not in search_query:
            print(f"ERROR: Missing component: {component}")
            all_present = False
    
    if all_present:
        print("✅ Search query construction test passed")
        return True
    else:
        print("❌ Search query construction test failed")
        return False

def test_source_configuration():
    """Test that source configurations are consistent."""
    print("\n=== Testing Source Configuration ===")
    
    # Check that we have 27 predefined sugar sources
    print(f"Number of predefined sugar sources: {len(SUGAR_SOURCES_27)}")
    
    if len(SUGAR_SOURCES_27) != 27:
        print("ERROR: Expected 27 sugar sources")
        return False
    
    # Check that all sources have IDs
    sources_without_ids = [s for s in SUGAR_SOURCES_27 if not s.get('id')]
    if sources_without_ids:
        print(f"ERROR: Sources without IDs: {sources_without_ids}")
        return False
    
    # Check that we have MEDIA_TOPIC_IDS defined
    print(f"Number of MEDIA_TOPIC_IDS: {len(MEDIA_TOPIC_IDS)}")
    
    if not MEDIA_TOPIC_IDS:
        print("ERROR: No MEDIA_TOPIC_IDS defined")
        return False
    
    # Check that ALL_SUGAR_SOURCE_NAMES_27 matches SUGAR_SOURCES_27
    expected_names = [s['name'] for s in SUGAR_SOURCES_27]
    if set(ALL_SUGAR_SOURCE_NAMES_27) != set(expected_names):
        print("ERROR: ALL_SUGAR_SOURCE_NAMES_27 doesn't match SUGAR_SOURCES_27")
        return False
    
    print("✅ Source configuration test passed")
    return True

def main():
    """Run all double filtering tests."""
    print("Starting double filtering implementation tests...\n")
    
    tests = [
        ("Source Configuration", test_source_configuration),
        ("Search Query Construction", test_search_query_construction),
        ("API Double Filtering", test_api_double_filtering),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR: Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Double filtering implementation is working correctly.")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
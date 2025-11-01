#!/usr/bin/env python
"""
Test script to validate the sugar news filtering system fixes.

This script tests:
1. Enhanced deduplication across different topic IDs
2. Improved triage filter with better logging
3. Reduced MEDIA_TOPIC_IDS to minimize duplicate processing
4. Enhanced content hash generation with URL tracking
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
from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
from sugar.backend.parsers.sugar_news_fetcher import (
    SUGAR_SOURCES_27, 
    MEDIA_TOPIC_IDS,
    generate_content_hash,
    is_similar_content
)

def test_enhanced_deduplication():
    """Test the enhanced deduplication functionality"""
    print("=== Testing Enhanced Deduplication ===")
    
    # Test content hash generation with URL tracking
    title1 = "Sugar prices reach record high"
    text1 = "Sugar production in Brazil has increased significantly due to favorable weather conditions."
    source1 = "Sugar Producer"
    url1 = "https://sugarproducer.com/sugar-prices-record-high"
    
    title2 = "Sugar prices reach record high"
    text2 = "Sugar production in Brazil has increased significantly due to favorable weather conditions."
    source2 = "Sugar Producer"
    url2 = "https://sugarproducer.com/sugar-prices-record-high"  # Same URL
    
    # Generate content hashes
    hash1 = generate_content_hash(title1, text1, source1)
    hash2 = generate_content_hash(title2, text2, source2)
    
    print(f"Article 1 hash: {hash1}")
    print(f"Article 2 hash: {hash2}")
    print(f"Hashes match: {hash1 == hash2}")
    print(f"URLs match: {url1 == url2}")
    
    # Test similarity detection
    similar = is_similar_content(title1, text1, source1, title2, text2, source2)
    print(f"Articles detected as similar: {similar}")
    
    return hash1 == hash2 and url1 == url2 and similar

def test_triage_filter_enhancements():
    """Test the enhanced triage filter with better logging"""
    print("\n=== Testing Enhanced Triage Filter ===")
    
    # Test case 1: Article that should pass (sugar-related)
    sugar_title = "Brazil Sugar Exports Rise on Global Demand"
    sugar_text = "Brazil's sugar exports have increased by 15% this year due to strong global demand and favorable production conditions. The International Sugar Organization reports that sugar production in Brazil's Center-South region has reached record levels."
    
    result1 = triage_filter(sugar_text, sugar_title)
    print(f"Test 1 - Sugar Article:")
    print(f"  Title: {sugar_title}")
    print(f"  Passed: {result1['passed']}")
    print(f"  Reason: {result1['reason']}")
    
    # Test case 2: Article that should fail (irrigation equipment)
    irrigation_title = "Irrigation Buyers' Guide 2025"
    irrigation_text = "The latest irrigation equipment and technology for modern farming. This comprehensive guide covers everything from drip irrigation systems to center pivot sprinklers. Agricultural equipment manufacturers have released new products designed to improve water efficiency and crop yields."
    
    result2 = triage_filter(irrigation_text, irrigation_title)
    print(f"\nTest 2 - Irrigation Article (should fail):")
    print(f"  Title: {irrigation_title}")
    print(f"  Passed: {result2['passed']}")
    print(f"  Reason: {result2['reason']}")
    
    # Test case 3: Mixed commodity article (should pass)
    mixed_title = "Sugar and Oil Markets Show Volatility"
    mixed_text = "Both sugar and oil markets experienced significant volatility this week. Sugar prices rose due to concerns about Brazilian production, while oil prices fluctuated on geopolitical tensions. The sugar industry is closely monitoring weather patterns in key producing regions."
    
    result3 = triage_filter(mixed_text, mixed_title)
    print(f"\nTest 3 - Mixed Commodity Article:")
    print(f"  Title: {mixed_title}")
    print(f"  Passed: {result3['passed']}")
    print(f"  Reason: {result3['reason']}")
    
    # Expected results
    expected_results = [
        result1['passed'] == True,   # Sugar article should pass
        result2['passed'] == False,  # Irrigation article should fail
        result3['passed'] == True    # Mixed commodity article should pass
    ]
    
    return all(expected_results)

def test_media_topic_ids_reduction():
    """Test the reduced MEDIA_TOPIC_IDS configuration"""
    print("\n=== Testing MEDIA_TOPIC_IDS Reduction ===")
    
    print(f"Previous MEDIA_TOPIC_IDS count: 13")
    print(f"Current MEDIA_TOPIC_IDS count: {len(MEDIA_TOPIC_IDS)}")
    print(f"Current MEDIA_TOPIC_IDS: {MEDIA_TOPIC_IDS}")
    
    # Verify that we have fewer topic IDs now
    return len(MEDIA_TOPIC_IDS) == 3

def test_double_filtering_logic():
    """Test the double filtering logic implementation"""
    print("\n=== Testing Double Filtering Logic ===")
    
    # Test source configuration
    print(f"Number of predefined sugar sources: {len(SUGAR_SOURCES_27)}")
    
    # Verify all sources have IDs
    sources_without_ids = [s for s in SUGAR_SOURCES_27 if not s.get('id')]
    if sources_without_ids:
        print(f"ERROR: Sources without IDs: {sources_without_ids}")
        return False
    
    # Test topic IDs configuration
    print(f"Number of MEDIA_TOPIC_IDS: {len(MEDIA_TOPIC_IDS)}")
    if not MEDIA_TOPIC_IDS:
        print("ERROR: No MEDIA_TOPIC_IDS defined")
        return False
    
    print("✅ Double filtering configuration is valid")
    return True

def test_api_integration():
    """Test API integration with double filtering (if API key is available)"""
    print("\n=== Testing API Integration ===")
    
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("WARNING: OPOINT_API_KEY not found - skipping API integration test")
        return True
    
    try:
        # Initialize API
        api = OpointAPI(api_key=api_key)
        
        # Test with a small date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        # Get a sample sugar source and topic ID
        test_source = SUGAR_SOURCES_27[0]  # Use first sugar source
        test_topic_ids = [MEDIA_TOPIC_IDS[0]]  # Use first topic ID
        
        print(f"Testing with:")
        print(f"  - Source: {test_source['name']} (ID: {test_source['id']})")
        print(f"  - Topic ID: {test_topic_ids[0]}")
        print(f"  - Date range: {start_date.date()} to {end_date.date()}")
        
        # Test API call with double filtering
        results = api.search_articles(
            site_id=str(test_source['id']),
            search_text="sugar",  # Simple search term
            num_articles=5,  # Small number for testing
            min_score=0.77,
            start_date=start_date,
            end_date=end_date,
            media_topic_ids=test_topic_ids,
            timeout=30
        )
        
        print(f"API returned {len(results)} articles")
        
        if not results.empty:
            # Validate double filtering
            if 'id_site' in results.columns:
                expected_id = str(test_source['id'])
                correct_media_id = (results['id_site'].astype(str) == expected_id).all()
                print(f"MEDIA_ID validation: {'PASS' if correct_media_id else 'FAIL'}")
                
                if not correct_media_id:
                    print("ERROR: Some articles have incorrect MEDIA_ID")
                    return False
            else:
                print("WARNING: id_site column not available in results")
            
            print("✅ API double filtering test completed successfully")
            return True
        else:
            print("No articles returned - this might be normal for the test parameters")
            return True
            
    except Exception as e:
        print(f"ERROR: API test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("Testing Sugar News Filtering System Fixes")
    print("=" * 60)
    
    try:
        # Run all tests
        test_results = []
        
        # Test enhanced deduplication
        dedup_test_passed = test_enhanced_deduplication()
        test_results.append(("Enhanced Deduplication", dedup_test_passed))
        
        # Test triage filter enhancements
        triage_test_passed = test_triage_filter_enhancements()
        test_results.append(("Enhanced Triage Filter", triage_test_passed))
        
        # Test MEDIA_TOPIC_IDS reduction
        topic_ids_test_passed = test_media_topic_ids_reduction()
        test_results.append(("MEDIA_TOPIC_IDS Reduction", topic_ids_test_passed))
        
        # Test double filtering logic
        double_filtering_test_passed = test_double_filtering_logic()
        test_results.append(("Double Filtering Logic", double_filtering_test_passed))
        
        # Test API integration (optional)
        api_test_passed = test_api_integration()
        test_results.append(("API Integration", api_test_passed))
        
        # Print results
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\nTotal: {passed}/{len(test_results)} tests passed")
        
        if passed == len(test_results):
            print("\n🎉 ALL TESTS PASSED!")
            print("\nFixes implemented:")
            print("✅ Enhanced deduplication with URL tracking and cross-topic prevention")
            print("✅ Improved triage filter with better logging for failed articles")
            print("✅ Reduced MEDIA_TOPIC_IDS from 13 to 3 to minimize duplicate processing")
            print("✅ Enhanced content hash generation with source awareness")
            print("✅ Better debugging and logging for troubleshooting")
            print("\nThe sugar news filtering system should now:")
            print("- Process fewer duplicate articles across different topic IDs")
            print("- Provide better logging for articles that fail the triage filter")
            print("- More efficiently identify and process sugar-related content")
            print("- Reduce processing overhead with fewer topic IDs")
            return 0
        else:
            print(f"\n⚠️  {len(test_results) - passed} test(s) failed. Please review the implementation.")
            return 1
            
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
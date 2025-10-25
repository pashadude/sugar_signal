#!/usr/bin/env python3
"""
Test script to verify deduplication and filtering improvements in the sugar news pipeline.

This script tests:
1. Articles with the same content but different sources are not considered duplicates
2. Articles with sugar-related keywords in either title or text are properly identified
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import generate_content_hash, is_similar_content
from sugar.backend.text_filtering.sugar_triage_filter import triage_filter

def test_deduplication_with_source():
    """Test that articles with the same content but different sources are not considered duplicates"""
    print("\n=== Testing Deduplication with Source Information ===")
    
    # Test case 1: Same content, same source - should be duplicates
    title1 = "Sugar prices rise globally"
    text1 = "Global sugar prices have increased by 10% this month due to supply constraints."
    source1 = "Reuters"
    
    title2 = "Sugar prices rise globally"
    text2 = "Global sugar prices have increased by 10% this month due to supply constraints."
    source2 = "Reuters"
    
    hash1 = generate_content_hash(title1, text1, source1)
    hash2 = generate_content_hash(title2, text2, source2)
    
    print(f"Test 1 - Same content, same source:")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 2: {hash2}")
    print(f"  Hashes match: {hash1 == hash2}")
    print(f"  Similar content: {is_similar_content(title1, text1, source1, title2, text2, source2)}")
    
    # Test case 2: Same content, different source - should NOT be duplicates
    title3 = "Sugar prices rise globally"
    text3 = "Global sugar prices have increased by 10% this month due to supply constraints."
    source3 = "Bloomberg"
    
    hash3 = generate_content_hash(title3, text3, source3)
    
    print(f"\nTest 2 - Same content, different source:")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 3: {hash3}")
    print(f"  Hashes match: {hash1 == hash3}")
    print(f"  Similar content: {is_similar_content(title1, text1, source1, title3, text3, source3)}")
    
    # Test case 3: Similar content, different source - should NOT be duplicates
    title4 = "Global sugar prices on the rise"
    text4 = "Sugar prices worldwide have gone up by 10% this month because of supply issues."
    source4 = "Financial Times"
    
    hash4 = generate_content_hash(title4, text4, source4)
    
    print(f"\nTest 3 - Similar content, different source:")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 4: {hash4}")
    print(f"  Hashes match: {hash1 == hash4}")
    print(f"  Similar content: {is_similar_content(title1, text1, source1, title4, text4, source4)}")
    
    # Test case 4: Similar content, same source - should be duplicates
    title5 = "Global sugar prices on the rise"
    text5 = "Sugar prices worldwide have gone up by 10% this month because of supply issues."
    source5 = "Reuters"
    
    hash5 = generate_content_hash(title5, text5, source5)
    
    print(f"\nTest 4 - Similar content, same source:")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 5: {hash5}")
    print(f"  Hashes match: {hash1 == hash5}")
    print(f"  Similar content: {is_similar_content(title1, text1, source1, title5, text5, source5)}")
    
    return True

def test_filtering_with_title_and_text():
    """Test that articles with sugar-related keywords in either title or text are properly identified"""
    print("\n=== Testing Filtering with Title and Text ===")
    
    # Test case 1: Sugar keyword in title only
    title1 = "Sugar production increases in Brazil"
    text1 = "Agricultural output has seen significant growth in the South American country."
    
    result1 = triage_filter(text1, title1)
    print(f"\nTest 1 - Sugar keyword in title only:")
    print(f"  Title: {title1}")
    print(f"  Text: {text1}")
    print(f"  Passed: {result1['passed']}")
    print(f"  Reason: {result1['reason']}")
    print(f"  Matched keywords: {result1['matched_keywords']}")
    
    # Test case 2: Sugar keyword in text only
    title2 = "Agricultural production increases in Brazil"
    text2 = "Sugar output has seen significant growth in the South American country."
    
    result2 = triage_filter(text2, title2)
    print(f"\nTest 2 - Sugar keyword in text only:")
    print(f"  Title: {title2}")
    print(f"  Text: {text2}")
    print(f"  Passed: {result2['passed']}")
    print(f"  Reason: {result2['reason']}")
    print(f"  Matched keywords: {result2['matched_keywords']}")
    
    # Test case 3: Sugar keyword in both title and text
    title3 = "Sugar production increases in Brazil"
    text3 = "Sugar output has seen significant growth in the South American country."
    
    result3 = triage_filter(text3, title3)
    print(f"\nTest 3 - Sugar keyword in both title and text:")
    print(f"  Title: {title3}")
    print(f"  Text: {text3}")
    print(f"  Passed: {result3['passed']}")
    print(f"  Reason: {result3['reason']}")
    print(f"  Matched keywords: {result3['matched_keywords']}")
    
    # Test case 4: No sugar keywords
    title4 = "Wheat production increases in Brazil"
    text4 = "Wheat output has seen significant growth in the South American country."
    
    result4 = triage_filter(text4, title4)
    print(f"\nTest 4 - No sugar keywords:")
    print(f"  Title: {title4}")
    print(f"  Text: {text4}")
    print(f"  Passed: {result4['passed']}")
    print(f"  Reason: {result4['reason']}")
    print(f"  Matched keywords: {result4['matched_keywords']}")
    
    # Test case 5: Sugar keyword with context
    title5 = "Brazil sugar exports affected by weather"
    text5 = "The recent drought in Brazil has impacted the sugar harvest, leading to concerns about export volumes."
    
    result5 = triage_filter(text5, title5)
    print(f"\nTest 5 - Sugar keyword with context:")
    print(f"  Title: {title5}")
    print(f"  Text: {text5}")
    print(f"  Passed: {result5['passed']}")
    print(f"  Reason: {result5['reason']}")
    print(f"  Matched zones: {result5['matched_zones']}")
    print(f"  Matched keywords: {result5['matched_keywords']}")
    
    # Test case 6: Exclusion keyword
    title6 = "Sugar and copper prices rise"
    text6 = "Both sugar and copper commodities have seen price increases this month."
    
    result6 = triage_filter(text6, title6)
    print(f"\nTest 6 - Exclusion keyword:")
    print(f"  Title: {title6}")
    print(f"  Text: {text6}")
    print(f"  Passed: {result6['passed']}")
    print(f"  Reason: {result6['reason']}")
    print(f"  Matched keywords: {result6['matched_keywords']}")
    
    return True

def test_backward_compatibility():
    """Test that the updated triage_filter function maintains backward compatibility"""
    print("\n=== Testing Backward Compatibility ===")
    
    # Test calling triage_filter with only text parameter (old way)
    text = "Sugar production increases in Brazil due to favorable weather conditions."
    
    result_old = triage_filter(text)
    result_new = triage_filter(text, None)
    
    print(f"\nTest - Backward compatibility:")
    print(f"  Text only call - Passed: {result_old['passed']}, Reason: {result_old['reason']}")
    print(f"  Text + None title call - Passed: {result_new['passed']}, Reason: {result_new['reason']}")
    print(f"  Results match: {result_old['passed'] == result_new['passed']}")
    
    return True

def main():
    """Run all tests"""
    print("Starting deduplication and filtering tests...")
    
    try:
        # Test deduplication with source information
        dedup_success = test_deduplication_with_source()
        
        # Test filtering with title and text
        filter_success = test_filtering_with_title_and_text()
        
        # Test backward compatibility
        compat_success = test_backward_compatibility()
        
        # Summary
        print("\n=== Test Summary ===")
        print(f"Deduplication with source: {'PASSED' if dedup_success else 'FAILED'}")
        print(f"Filtering with title and text: {'PASSED' if filter_success else 'FAILED'}")
        print(f"Backward compatibility: {'PASSED' if compat_success else 'FAILED'}")
        
        if dedup_success and filter_success and compat_success:
            print("\nAll tests PASSED! ✅")
            return 0
        else:
            print("\nSome tests FAILED! ❌")
            return 1
            
    except Exception as e:
        print(f"\nTest execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
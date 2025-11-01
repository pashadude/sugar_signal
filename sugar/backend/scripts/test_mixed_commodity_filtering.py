#!/usr/bin/env python3
"""
Test script to verify that mixed commodity articles are now accepted
by the updated sugar triage filter logic.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.text_filtering.sugar_triage_filter import triage_filter

def test_mixed_commodity_article():
    """Test the user's example: mixed commodity article should now be accepted"""
    
    print("=== Testing Mixed Commodity Article Filtering ===\n")
    
    # Test case from user's example
    test_title = "Sugar and oil prices fluctuate"
    test_text = "Both sugar and copper commodities have seen price increases this month."
    
    print(f"Test Article:")
    print(f"Title: {test_title}")
    print(f"Text: {test_text}\n")
    
    # Apply triage filter
    result = triage_filter(test_text, test_title)
    
    print("Filter Results:")
    print(f"Passed: {result['passed']}")
    print(f"Reason: {result['reason']}")
    print(f"Matched Zones: {result['matched_zones']}")
    print(f"Matched Keywords: {result['matched_keywords']}")
    print()
    
    # Verify expected behavior
    if result['passed']:
        print("✅ SUCCESS: Mixed commodity article was ACCEPTED as expected")
        return True
    else:
        print("❌ FAILURE: Mixed commodity article was REJECTED (should be accepted)")
        return False

def test_non_sugar_article():
    """Test that articles without sugar keywords are still properly rejected"""
    
    print("=== Testing Non-Sugar Article (should be rejected) ===\n")
    
    # Test case: article without sugar keywords
    test_title = "Copper and oil prices fluctuate"
    test_text = "Both copper and oil commodities have seen price increases this month."
    
    print(f"Test Article:")
    print(f"Title: {test_title}")
    print(f"Text: {test_text}\n")
    
    # Apply triage filter
    result = triage_filter(test_text, test_title)
    
    print("Filter Results:")
    print(f"Passed: {result['passed']}")
    print(f"Reason: {result['reason']}")
    print(f"Matched Zones: {result['matched_zones']}")
    print(f"Matched Keywords: {result['matched_keywords']}")
    print()
    
    # Verify expected behavior
    if not result['passed']:
        print("✅ SUCCESS: Non-sugar article was REJECTED as expected")
        return True
    else:
        print("❌ FAILURE: Non-sugar article was ACCEPTED (should be rejected)")
        return False

def test_pure_sugar_article():
    """Test that pure sugar articles are still accepted"""
    
    print("=== Testing Pure Sugar Article (should be accepted) ===\n")
    
    # Test case: pure sugar article
    test_title = "Sugar prices reach 5-year high"
    test_text = "Sugar production in Brazil has increased significantly due to favorable weather conditions."
    
    print(f"Test Article:")
    print(f"Title: {test_title}")
    print(f"Text: {test_text}\n")
    
    # Apply triage filter
    result = triage_filter(test_text, test_title)
    
    print("Filter Results:")
    print(f"Passed: {result['passed']}")
    print(f"Reason: {result['reason']}")
    print(f"Matched Zones: {result['matched_zones']}")
    print(f"Matched Keywords: {result['matched_keywords']}")
    print()
    
    # Verify expected behavior
    if result['passed']:
        print("✅ SUCCESS: Pure sugar article was ACCEPTED as expected")
        return True
    else:
        print("❌ FAILURE: Pure sugar article was REJECTED (should be accepted)")
        return False

def main():
    """Run all test cases"""
    
    print("Testing updated sugar triage filter logic for mixed commodity articles\n")
    
    test_results = []
    
    # Run all test cases
    test_results.append(test_mixed_commodity_article())
    print("\n" + "="*60 + "\n")
    
    test_results.append(test_non_sugar_article())
    print("\n" + "="*60 + "\n")
    
    test_results.append(test_pure_sugar_article())
    print("\n" + "="*60 + "\n")
    
    # Summary
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print("=== TEST SUMMARY ===")
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! The filtering logic is working correctly.")
        print("✅ Mixed commodity articles are now accepted")
        print("✅ Non-sugar articles are still rejected")
        print("✅ Pure sugar articles are still accepted")
        return 0
    else:
        print("❌ SOME TESTS FAILED! Please check the filtering logic.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
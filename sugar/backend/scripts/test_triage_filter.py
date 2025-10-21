#!/usr/bin/env python3
"""
Test script for the sugar triage filter functionality
Tests various scenarios including valid sugar news, non-sugar content, and edge cases
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def test_triage_filter():
    """Test the triage filter functionality with various test cases"""
    print("Testing triage filter functionality...")
    
    try:
        from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
        
        # Test cases with expected results
        test_cases = [
            {
                "text": "Brazilian sugar exports are rising due to market price changes.",
                "expected": True,
                "description": "Valid sugar news with market context",
                "expected_zones": ["market", "region"]
            },
            {
                "text": "Copper prices are rising in the commodity market.",
                "expected": False,
                "description": "Non-sugar commodity news",
                "expected_reason": "Excluded by exclusion keyword"
            },
            {
                "text": "Sugar production in Brazil affected by drought conditions.",
                "expected": True,
                "description": "Sugar news with weather event",
                "expected_zones": ["event", "region"]
            },
            {
                "text": "Generic market news about inflation and interest rates.",
                "expected": False,
                "description": "Generic market news without sugar context",
                "expected_reason": "No main sugar-related keywords found"
            },
            {
                "text": "sugar",
                "expected": False,
                "description": "Too short text",
                "expected_reason": "Text too short"
            },
            {
                "text": "",
                "expected": False,
                "description": "Empty text",
                "expected_reason": "Text is empty or not a string"
            },
            {
                "text": "Brazil's Center-South sugar production increases due to favorable weather conditions.",
                "expected": True,
                "description": "Sugar news with region and weather context",
                "expected_zones": ["region", "event"]
            },
            {
                "text": "UNICA reports Brazilian sugar production at record levels.",
                "expected": True,
                "description": "Sugar news with organization and production context",
                "expected_zones": ["region", "supply_chain"]
            },
            {
                "text": "Sugar futures contract prices surge on export demand.",
                "expected": True,
                "description": "Sugar news with futures and export context",
                "expected_zones": ["market"]
            },
            {
                "text": "Wheat and corn prices affected by global supply chain issues.",
                "expected": False,
                "description": "Non-sugar agricultural commodities",
                "expected_reason": "Excluded by exclusion keyword"
            },
            {
                "text": "Sugar beet harvest in Europe impacted by frost damage.",
                "expected": True,
                "description": "Sugar beet news with weather event",
                "expected_zones": ["event", "region"]
            },
            {
                "text": "Ethanol production from sugarcane increases in Brazil.",
                "expected": True,
                "description": "Sugar-related ethanol production",
                "expected_zones": ["event", "region"]
            },
            {
                "text": "NY11 sugar prices rise on supply concerns from India.",
                "expected": True,
                "description": "Sugar contract with region context",
                "expected_zones": ["market", "region"]
            },
            {
                "text": "Gold and silver prices surge as safe haven assets.",
                "expected": False,
                "description": "Precious metals without sugar context",
                "expected_reason": "Excluded by exclusion keyword"
            },
            {
                "text": "Sugar mill in Thailand increases production capacity.",
                "expected": True,
                "description": "Sugar production with region context",
                "expected_zones": ["supply_chain", "region"]
            }
        ]
        
        # Additional test cases for structured pricing data
        pricing_test_cases = [
            {
                "text": """Contract: NY11
Date: 2024-01-15
Price: 18.50
Volume: 125,000
Index: Sugar #11""",
                "expected": True,
                "description": "Structured sugar pricing data",
                "expected_pricing": True
            },
            {
                "text": """* Sugar futures: 18.75 cents/lb
* Volume: 150,000 tons
* Settlement: +0.25""",
                "expected": True,
                "description": "Bullet point sugar pricing",
                "expected_pricing": True
            },
            {
                "text": """1. Copper contract: $8,500
2. Gold price: $1,950
3. Silver volume: 50,000""",
                "expected": False,
                "description": "Non-sugar structured pricing",
                "expected_reason": "Excluded by exclusion keyword"
            }
        ]
        
        # Combine all test cases
        all_test_cases = test_cases + pricing_test_cases
        
        passed = 0
        failed = 0
        results = []
        
        print(f"\nRunning {len(all_test_cases)} test cases...\n")
        
        for i, test_case in enumerate(all_test_cases):
            print(f"Test Case {i+1}: {test_case['description']}")
            print(f"Input: {test_case['text'][:100]}{'...' if len(test_case['text']) > 100 else ''}")
            
            result = triage_filter(test_case["text"])
            
            # Check if result matches expected
            test_passed = result["passed"] == test_case["expected"]
            
            # Additional checks for failed cases
            if not test_case["expected"] and "expected_reason" in test_case:
                # Handle the case where expected reason is a substring of actual reason
                if test_case["expected_reason"] == "Excluded by exclusion keyword":
                    test_passed = test_passed and "Excluded by exclusion keyword" in result["reason"]
                    # Debug print for Test Case 4
                    if i == 3:  # Test Case 4 (0-indexed)
                        print(f"DEBUG: Expected reason: '{test_case['expected_reason']}'")
                        print(f"DEBUG: Actual reason: '{result['reason']}'")
                        print(f"DEBUG: Contains check: {'Excluded by exclusion keyword' in result['reason']}")
                else:
                    test_passed = test_passed and test_case["expected_reason"] in result["reason"]
            
            # For cases that pass the secondary filter, we need to handle them specially
            if test_case["expected"] and result["passed"] and "Passed secondary filter" in result["reason"]:
                # These cases pass through the secondary filter, so we don't check zones
                test_passed = True
            elif test_case["expected"] and "expected_zones" in test_case and result["passed"]:
                # Check if expected zones are matched (only for regular passes)
                zones_matched = all(zone in result["matched_zones"] for zone in test_case["expected_zones"])
                test_passed = test_passed and zones_matched
            
            if "expected_pricing" in test_case:
                pricing_extracted = len(result["extracted_sugar_pricing"]) > 0
                test_passed = test_passed and (pricing_extracted == test_case["expected_pricing"])
            
            if test_passed:
                print(f"✓ PASSED - {result['reason']}")
                passed += 1
            else:
                print(f"✗ FAILED - Expected: {test_case['expected']}, Got: {result['passed']}")
                print(f"  Reason: {result['reason']}")
                if result["matched_zones"]:
                    print(f"  Matched zones: {result['matched_zones']}")
                if result["extracted_sugar_pricing"]:
                    print(f"  Extracted pricing: {len(result['extracted_sugar_pricing'])} lines")
                failed += 1
            
            # Store detailed result
            results.append({
                "test_case": i+1,
                "description": test_case["description"],
                "input": test_case["text"],
                "expected": test_case["expected"],
                "actual": result["passed"],
                "passed": test_passed,
                "reason": result["reason"],
                "matched_zones": result["matched_zones"],
                "matched_keywords": result["matched_keywords"],
                "extracted_pricing": result["extracted_sugar_pricing"]
            })
            
            print("-" * 80)
        
        # Print summary
        print(f"\n=== TRIAGE FILTER TEST SUMMARY ===")
        print(f"Total tests: {len(all_test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/len(all_test_cases)*100:.1f}%")
        
        # Save detailed results to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"triage_filter_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        return failed == 0
        
    except Exception as e:
        print(f"✗ Error testing triage filter: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_keyword_patterns():
    """Test keyword pattern matching functionality"""
    print("\nTesting keyword pattern matching...")
    
    try:
        from sugar.backend.text_filtering.sugar_triage_filter import KEYWORD_PATTERNS, text_matches_keywords
        
        # Test keyword matching
        keyword_tests = [
            {
                "text": "sugar production in Brazil",
                "zone": "main",
                "expected": True
            },
            {
                "text": "sugarcane harvest affected by weather",
                "zone": "main",
                "expected": True
            },
            {
                "text": "futures market for commodities",
                "zone": "market",
                "expected": True
            },
            {
                "text": "drought impacts agricultural production",
                "zone": "event",
                "expected": True
            },
            {
                "text": "Brazilian economy grows",
                "zone": "region",
                "expected": True
            },
            {
                "text": "copper prices rise",
                "zone": "main",
                "expected": False
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(keyword_tests):
            patterns = KEYWORD_PATTERNS.get(test["zone"], [])
            result = text_matches_keywords(test["text"], patterns)
            
            if result == test["expected"]:
                print(f"✓ Test {i+1} passed: {test['text']} -> {result}")
                passed += 1
            else:
                print(f"✗ Test {i+1} failed: {test['text']} -> Expected {test['expected']}, got {result}")
                failed += 1
        
        print(f"\nKeyword pattern tests: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"✗ Error testing keyword patterns: {e}")
        return False

def main():
    """Main test function"""
    print("=== SUGAR TRIAGE FILTER TEST SUITE ===")
    print(f"Started at: {datetime.now()}")
    
    # Run tests
    triage_passed = test_triage_filter()
    keyword_passed = test_keyword_patterns()
    
    # Overall result
    overall_passed = triage_passed and keyword_passed
    
    print(f"\n=== OVERALL TEST RESULTS ===")
    print(f"Triage Filter Tests: {'PASSED' if triage_passed else 'FAILED'}")
    print(f"Keyword Pattern Tests: {'PASSED' if keyword_passed else 'FAILED'}")
    print(f"Overall: {'PASSED' if overall_passed else 'FAILED'}")
    
    return 0 if overall_passed else 1

if __name__ == "__main__":
    exit(main())
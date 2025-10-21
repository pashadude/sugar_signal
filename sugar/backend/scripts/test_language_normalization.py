#!/usr/bin/env python3
"""
Test script for the language normalization pipeline
Tests various scenarios including translation, typo correction, slang mapping, and edge cases
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

def test_language_normalization():
    """Test the language normalization pipeline functionality"""
    print("Testing language normalization pipeline...")
    
    try:
        from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline
        
        # Initialize the pipeline
        pipeline = LanguageNormalizationPipeline()
        
        # Test cases with expected results
        test_cases = [
            {
                "text": "u r gr8! lol.",
                "expected_features": ["slang_mapping", "punctuation_normalization"],
                "description": "Slang and abbreviations"
            },
            {
                "text": "I relly lik this prodct, its awsome!!!",
                "expected_features": ["typo_correction"],
                "description": "Typo-rich input"
            },
            {
                "text": "Wait.....what???!!!   No way!!!",
                "expected_features": ["punctuation_normalization"],
                "description": "Punctuation/formatting noise"
            },
            {
                "text": "namaste dosto, kaise ho?",
                "expected_features": ["translation", "transliteration"],
                "description": "Transliterated input (Hindi in Latin script)"
            },
            {
                "text": "Dr. Smith is gr8 at his job.",
                "expected_features": ["slang_mapping", "punctuation_normalization"],
                "description": "Mixed content with abbreviations"
            },
            {
                "text": "C'est la vie! Je t'aime beaucoup.",
                "expected_features": ["translation"],
                "description": "French text"
            },
            {
                "text": "Hola amigo, how r u today?",
                "expected_features": ["slang_mapping"],
                "description": "Mixed-language input"
            },
            {
                "text": "I ❤️ this! gr8 job 👍",
                "expected_features": ["slang_mapping", "emoji_handling"],
                "description": "Emojis and symbols"
            },
            {
                "text": "sugar",
                "expected_features": ["minimal_processing"],
                "description": "Simple single word"
            },
            {
                "text": "",
                "expected_features": ["empty_handling"],
                "description": "Empty text"
            }
        ]
        
        # Test cases for structured pricing data normalization
        pricing_test_cases = [
            {
                "lines": [
                    "Contract: NY11",
                    "Date: 2024-01-15",
                    "Price: 18.50",
                    "Volume: 125,000",
                    "Index: Sugar #11"
                ],
                "expected_fields": ["contract", "date", "price", "volume", "index"],
                "description": "Structured sugar pricing data"
            },
            {
                "lines": [
                    "* Sugar futures: 18.75 cents/lb",
                    "* Volume: 150,000 tons",
                    "* Settlement: +0.25"
                ],
                "expected_fields": ["price", "volume"],
                "description": "Bullet point sugar pricing"
            },
            {
                "lines": [
                    "1. Copper contract: $8,500",
                    "2. Gold price: $1,950",
                    "3. Silver volume: 50,000"
                ],
                "expected_fields": [],  # Should not extract non-sugar data
                "description": "Non-sugar structured pricing"
            }
        ]
        
        passed = 0
        failed = 0
        results = []
        
        print(f"\nRunning {len(test_cases)} text normalization test cases...\n")
        
        # Test text normalization
        for i, test_case in enumerate(test_cases):
            print(f"Test Case {i+1}: {test_case['description']}")
            print(f"Input: {test_case['text']}")
            
            try:
                normalized = pipeline.normalize(test_case["text"])
                print(f"Output: {normalized}")
                
                # Basic validation - should return a string
                test_passed = isinstance(normalized, str)
                
                # Check for expected features (simplified checks)
                if "typo_correction" in test_case["expected_features"]:
                    # Should be different from input (typos corrected)
                    test_passed = test_passed and normalized != test_case["text"]
                
                if "punctuation_normalization" in test_case["expected_features"]:
                    # Should have normalized punctuation
                    test_passed = test_passed and "!!!" not in normalized and "..." not in normalized
                
                if "empty_handling" in test_case["expected_features"]:
                    # Should handle empty text gracefully
                    test_passed = test_passed and normalized == ""
                
                if test_passed:
                    print(f"✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED - Expected features: {test_case['expected_features']}")
                    failed += 1
                
                # Store detailed result
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "input": test_case["text"],
                    "output": normalized,
                    "expected_features": test_case["expected_features"],
                    "passed": test_passed,
                    "type": "text_normalization"
                })
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "input": test_case["text"],
                    "error": str(e),
                    "expected_features": test_case["expected_features"],
                    "passed": False,
                    "type": "text_normalization"
                })
            
            print("-" * 80)
        
        print(f"\nRunning {len(pricing_test_cases)} pricing data normalization test cases...\n")
        
        # Test pricing data normalization
        for i, test_case in enumerate(pricing_test_cases):
            print(f"Pricing Test Case {i+1}: {test_case['description']}")
            print(f"Input lines: {test_case['lines']}")
            
            try:
                normalized_pricing = pipeline.normalize(sugar_pricing_lines=test_case["lines"])
                print(f"Normalized pricing: {normalized_pricing}")
                
                # Basic validation - should return a list
                test_passed = isinstance(normalized_pricing, list)
                
                # Check for expected fields
                if test_case["expected_fields"]:
                    extracted_fields = []
                    for item in normalized_pricing:
                        if isinstance(item, dict):
                            extracted_fields.extend([k for k, v in item.items() if v is not None])
                    
                    # Should have at least some of the expected fields
                    if test_case["expected_fields"]:
                        test_passed = test_passed and any(field in extracted_fields for field in test_case["expected_fields"])
                else:
                    # For non-sugar data, should still return a list but possibly empty
                    test_passed = test_passed and isinstance(normalized_pricing, list)
                
                if test_passed:
                    print(f"✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED - Expected fields: {test_case['expected_fields']}")
                    failed += 1
                
                # Store detailed result
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "input": test_case["lines"],
                    "output": normalized_pricing,
                    "expected_fields": test_case["expected_fields"],
                    "passed": test_passed,
                    "type": "pricing_normalization"
                })
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "input": test_case["lines"],
                    "error": str(e),
                    "expected_fields": test_case["expected_fields"],
                    "passed": False,
                    "type": "pricing_normalization"
                })
            
            print("-" * 80)
        
        # Print summary
        total_tests = len(test_cases) + len(pricing_test_cases)
        print(f"\n=== LANGUAGE NORMALIZATION TEST SUMMARY ===")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/total_tests*100:.1f}%")
        
        # Save detailed results to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"language_normalization_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        return failed == 0
        
    except Exception as e:
        print(f"✗ Error testing language normalization: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_components():
    """Test individual components of the pipeline"""
    print("\nTesting individual pipeline components...")
    
    try:
        from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline
        
        pipeline = LanguageNormalizationPipeline()
        
        # Test individual methods
        component_tests = [
            {
                "method": "_normalize_punctuation",
                "input": "Wait.....what???!!!   No way!!!",
                "expected": "Wait.what! No way!",
                "description": "Punctuation normalization"
            },
            {
                "method": "_handle_edge_cases",
                "input": "namaste dosto, gr8",
                "expected": "hello dosto, great",  # Expected transliteration mapping
                "description": "Edge case handling"
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(component_tests):
            print(f"Component Test {i+1}: {test['description']}")
            print(f"Input: {test['input']}")
            
            try:
                if hasattr(pipeline, test["method"]):
                    method = getattr(pipeline, test["method"])
                    result = method(test["input"])
                    print(f"Output: {result}")
                    print(f"Expected: {test['expected']}")
                    
                    # Simple equality check (can be relaxed for real-world scenarios)
                    test_passed = result == test["expected"]
                    
                    if test_passed:
                        print(f"✓ PASSED")
                        passed += 1
                    else:
                        print(f"✗ FAILED")
                        failed += 1
                else:
                    print(f"✗ Method {test['method']} not found")
                    failed += 1
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
            
            print("-" * 40)
        
        print(f"\nComponent tests: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"✗ Error testing pipeline components: {e}")
        return False

def main():
    """Main test function"""
    print("=== LANGUAGE NORMALIZATION TEST SUITE ===")
    print(f"Started at: {datetime.now()}")
    
    # Run tests
    normalization_passed = test_language_normalization()
    components_passed = test_pipeline_components()
    
    # Overall result
    overall_passed = normalization_passed and components_passed
    
    print(f"\n=== OVERALL TEST RESULTS ===")
    print(f"Language Normalization Tests: {'PASSED' if normalization_passed else 'FAILED'}")
    print(f"Component Tests: {'PASSED' if components_passed else 'FAILED'}")
    print(f"Overall: {'PASSED' if overall_passed else 'FAILED'}")
    
    return 0 if overall_passed else 1

if __name__ == "__main__":
    exit(main())
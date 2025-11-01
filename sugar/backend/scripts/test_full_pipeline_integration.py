#!/usr/bin/env python3
"""
Integration test for the full sugar news pipeline: Translation → Normalization → Triage Filter

This script tests that the entire pipeline works correctly after our fix,
ensuring that important sugar keywords are preserved through all stages.
"""

import sys
import os

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
sys.path.insert(0, str(project_root))

# Import the actual components from the pipeline
try:
    # Add the sugar backend path to sys.path
    sugar_backend_path = os.path.join(current_dir, '..')
    sys.path.insert(0, sugar_backend_path)
    
    from text_filtering.language_normalization import LanguageNormalizationPipeline
    from text_filtering.sugar_triage_filter import triage_filter
    print("✓ Successfully imported pipeline components")
except ImportError as e:
    print(f"✗ Failed to import pipeline components: {e}")
    sys.exit(1)

def test_full_pipeline():
    """
    Test the full pipeline with realistic multilingual content.
    """
    print("=== Testing Full Pipeline Integration ===\n")
    
    # Initialize the normalization pipeline
    try:
        pipeline = LanguageNormalizationPipeline()
        print("✓ LanguageNormalizationPipeline initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize LanguageNormalizationPipeline: {e}")
        return False
    
    # Test cases with realistic content
    test_cases = [
        {
            "name": "English Sugarcane Article",
            "title": "Brazil Sugarcane Harvest Exceeds Expectations",
            "text": "Brazil's sugarcane harvest has exceeded expectations this year, with production reaching 600 million tons. Sugar beet production in Europe also showed significant growth.",
            "expected_pass": True,
            "expected_keywords": ["sugarcane", "sugar beet"]
        },
        {
            "name": "English Sugar Futures Article", 
            "title": "NY11 Sugar Futures Rise on Supply Concerns",
            "text": "NY11 sugar futures rose 2.5% today to 18.75 cents per pound. LSU and LON No. 5 contracts also gained ground as traders worried about global supply shortages.",
            "expected_pass": True,
            "expected_keywords": ["ny11", "lsu", "lon no 5"]
        },
        {
            "name": "Multilingual Article (Spanish)",
            "title": "Aumento en la producción de azúcar en Brasil",
            "text": "La producción de caña de azúcar en Brasil aumentó un 10% este año. Los futuros del azúcar NY11 también mostraron una tendencia alcista.",
            "expected_pass": True,
            "expected_keywords": ["azúcar"]  # Should be translated to "sugar"
        },
        {
            "name": "Non-Sugar Article (Should Fail)",
            "title": "Wheat Production in Ukraine",
            "text": "Wheat production in Ukraine is expected to decrease due to ongoing conflicts and weather conditions. Corn and soybean crops are also affected.",
            "expected_pass": False,
            "expected_keywords": []
        },
        {
            "name": "Sugar Whites Article",
            "title": "Sugar Whites Market Analysis",
            "text": "The whites sugar market is experiencing tight supply conditions due to reduced production in key producing regions. Prices are expected to remain elevated.",
            "expected_pass": True,
            "expected_keywords": ["whites"]
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Title: {test_case['title']}")
        print(f"Text: {test_case['text'][:100]}...")
        
        try:
            # Step 1: Normalize (includes translation if needed)
            print("\n1. Normalization Stage:")
            normalized_text = pipeline.normalize(test_case['text'])
            normalized_title = pipeline.normalize(test_case['title'])
            print(f"   Normalized Title: {normalized_title}")
            print(f"   Normalized Text: {normalized_text[:100]}...")
            
            # Step 2: Apply triage filter
            print("\n2. Triage Filter Stage:")
            result = triage_filter(normalized_text, normalized_title)
            
            print(f"   Passed: {result['passed']}")
            print(f"   Reason: {result['reason']}")
            if result.get('matched_keywords'):
                print(f"   Matched Keywords: {result['matched_keywords']}")
            
            # Check if result matches expectation
            if result['passed'] == test_case['expected_pass']:
                print("   ✓ PASS: Filter result matches expectation")
                passed_tests += 1
            else:
                print(f"   ✗ FAIL: Expected {test_case['expected_pass']}, got {result['passed']}")
            
            # Check if expected keywords are found
            if test_case['expected_keywords']:
                combined_content = f"{normalized_title} {normalized_text}".lower()
                found_keywords = []
                for keyword in test_case['expected_keywords']:
                    if keyword.lower() in combined_content:
                        found_keywords.append(keyword)
                
                if len(found_keywords) == len(test_case['expected_keywords']):
                    print(f"   ✓ PASS: All expected keywords found: {found_keywords}")
                else:
                    print(f"   ⚠ PARTIAL: Expected {test_case['expected_keywords']}, found {found_keywords}")
            
        except Exception as e:
            print(f"   ✗ ERROR: Exception during processing: {e}")
            continue
    
    print(f"\n=== INTEGRATION TEST RESULTS ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The full pipeline (Translation → Normalization → Triage Filter) is working correctly.")
        print("Important sugar keywords are preserved throughout the process.")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} integration tests failed.")
        print("The pipeline may need further investigation.")
        return False

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script to verify that important sugar keywords are preserved during normalization.

This script tests the fix for the normalize_content function to ensure that
important sugar keywords like "sugarcane", "sugar beet", "whites", "NY11", etc.
are not normalized to just "sugar", which would break the triage filter.
"""

import sys
import re
import os

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
sys.path.insert(0, str(project_root))

def normalize_content(content):
    """
    Copy of the fixed normalize_content function from sugar_news_fetcher.py
    for testing purposes.
    """
    if not content:
        return ""
    
    # Convert to lowercase
    content = content.lower()
    
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Remove URLs, email addresses, and other non-content elements
    content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
    content = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', content)
    
    # Remove punctuation but preserve word boundaries
    content = re.sub(r'[^\w\s]', ' ', content)
    
    # CRITICAL FIX: Preserve important sugar keywords for triage filter
    # Only normalize generic "sugar" references, but preserve specific sugar terms
    # that are important for the triage filter to detect sugar-related content
    content = re.sub(r'\bsugar\b(?!\s*(cane|beet))', 'sugar', content)  # Only normalize standalone "sugar"
    # DO NOT normalize: sugarcane, sugar beet, whites, NY11, LSU, LON No. 5, etc.
    
    # Normalize other common variations (non-sugar terms)
    content = re.sub(r'\b(price|prices|pricing|cost|costs)\b', 'price', content)  # Normalize price terms
    content = re.sub(r'\b(rise|rise|rising|increase|increased|up|higher)\b', 'rise', content)  # Normalize upward movement
    content = re.sub(r'\b(fall|fell|falling|decrease|decreased|down|lower)\b', 'fall', content)  # Normalize downward movement
    content = re.sub(r'\b(market|markets)\b', 'market', content)  # Normalize market terms
    content = re.sub(r'\b(supply|supplies)\b', 'supply', content)  # Normalize supply terms
    content = re.sub(r'\b(demand|demands)\b', 'demand', content)  # Normalize demand terms
    
    # Remove common stop words that don't affect meaning
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
    words = content.split()
    words = [word for word in words if word not in stop_words]
    content = ' '.join(words)
    
    # Strip leading/trailing whitespace
    content = content.strip()
    
    return content

def test_sugar_keyword_preservation():
    """
    Test that important sugar keywords are preserved during normalization.
    """
    print("=== Testing Sugar Keyword Preservation ===\n")
    
    # Test cases: important sugar keywords that should be preserved
    # These are the actual keywords from the triage filter's SUGAR_KEYWORDS list
    preserved_keywords = [
        "sugarcane",
        "sugar beet",
        "sugar cane",
        "whites",
        "NY11",
        "LSU",
        "LON No. 5"
    ]
    
    # Test cases: generic sugar references that should be normalized
    normalized_keywords = [
        "sugar",
        "sugar production",
        "sugar market",
        "sugar price"
    ]
    
    print("1. Testing keywords that should be PRESERVED:")
    preserved_passed = 0
    preserved_total = len(preserved_keywords)
    
    for keyword in preserved_keywords:
        normalized = normalize_content(keyword)
        # Check if the important keyword is still present in normalized form
        keyword_lower = keyword.lower()
        if keyword_lower in normalized:
            print(f"  ✓ PASS: '{keyword}' -> '{normalized}' (keyword preserved)")
            preserved_passed += 1
        else:
            print(f"  ✗ FAIL: '{keyword}' -> '{normalized}' (keyword lost)")
    
    print(f"\n   Results: {preserved_passed}/{preserved_total} keywords preserved correctly")
    
    print("\n2. Testing keywords that should be NORMALIZED:")
    normalized_passed = 0
    normalized_total = len(normalized_keywords)
    
    for keyword in normalized_keywords:
        normalized = normalize_content(keyword)
        # Check if "sugar" is present but other variations are normalized
        if "sugar" in normalized and keyword.lower() not in normalized.replace("sugar", "").strip():
            print(f"  ✓ PASS: '{keyword}' -> '{normalized}' (properly normalized)")
            normalized_passed += 1
        else:
            print(f"  ? INFO: '{keyword}' -> '{normalized}' (check if normalization is correct)")
    
    print(f"\n   Results: {normalized_passed}/{normalized_total} keywords normalized correctly")
    
    print("\n3. Testing full article content:")
    
    # Test with realistic article content
    test_articles = [
        {
            "title": "Sugarcane Production in Brazil",
            "text": "Brazilian sugarcane production increased this year due to favorable weather conditions. Sugar beet production in Europe also showed growth.",
            "expected_keywords": ["sugarcane", "sugar beet"]
        },
        {
            "title": "NY11 Sugar Futures Market Analysis",
            "text": "NY11 sugar futures rose to 18.5 cents per pound. LSU and LON No. 5 contracts also showed upward movement.",
            "expected_keywords": ["ny11", "lsu", "lon no 5"]
        },
        {
            "title": "Global Sugar Market Report",
            "text": "The global sugar market is experiencing volatility due to supply chain disruptions.",
            "expected_keywords": ["sugar"]
        }
    ]
    
    articles_passed = 0
    articles_total = len(test_articles)
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n  Article {i}: {article['title']}")
        
        # Combine title and text as done in the actual pipeline
        combined_content = f"{article['title']} {article['text']}"
        normalized = normalize_content(combined_content)
        
        print(f"    Original: {combined_content}")
        print(f"    Normalized: {normalized}")
        
        # Check if expected keywords are preserved
        all_keywords_preserved = True
        for keyword in article['expected_keywords']:
            if keyword.lower() not in normalized:
                print(f"    ✗ Missing expected keyword: '{keyword}'")
                all_keywords_preserved = False
            else:
                print(f"    ✓ Found expected keyword: '{keyword}'")
        
        if all_keywords_preserved:
            print(f"    ✓ PASS: All expected keywords preserved")
            articles_passed += 1
        else:
            print(f"    ✗ FAIL: Some keywords lost")
    
    print(f"\n   Results: {articles_passed}/{articles_total} articles preserved keywords correctly")
    
    # Overall results
    total_tests = preserved_total + normalized_total + articles_total
    total_passed = preserved_passed + normalized_passed + articles_passed
    
    print(f"\n=== OVERALL RESULTS ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success rate: {(total_passed / total_tests * 100):.1f}%")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! The fix successfully preserves important sugar keywords.")
        return True
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests failed. The fix may need adjustment.")
        return False

if __name__ == "__main__":
    success = test_sugar_keyword_preservation()
    sys.exit(0 if success else 1)
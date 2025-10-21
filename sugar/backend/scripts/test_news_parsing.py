#!/usr/bin/env python3
"""
Test script for the news parsing and HTML cleaning functionality
Tests various scenarios including HTML cleaning, keyword matching, query building, and article ID generation
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import hashlib

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def test_html_cleaning():
    """Test HTML cleaning functionality"""
    print("Testing HTML cleaning functionality...")
    
    try:
        from sugar.backend.parsers.news_parser import clean_html
        
        # Test cases with expected results
        test_cases = [
            {
                "html": "<p>This is a <strong>test</strong> paragraph with <a href='#'>links</a>.</p>",
                "expected": "This is a test paragraph with links.",
                "description": "Basic HTML tags"
            },
            {
                "html": "<div class='article'><h1>Title</h1><p>Content<br/>with<br/>line breaks</p></div>",
                "expected": "Title Content with line breaks",
                "description": "Nested HTML with line breaks"
            },
            {
                "html": "Text with   multiple    spaces   and\t\ttabs",
                "expected": "Text with multiple spaces and tabs",
                "description": "Whitespace normalization"
            },
            {
                "html": "<script>alert('test');</script><style>body{color:red;}</style><p>Content</p>",
                "expected": "Content",
                "description": "Script and style tag removal"
            },
            {
                "html": "<!-- Comment -->Visible text<!-- Another comment -->",
                "expected": "Visible text",
                "description": "HTML comment removal"
            },
            {
                "html": "Plain text without HTML",
                "expected": "Plain text without HTML",
                "description": "Plain text (no HTML)"
            },
            {
                "html": "",
                "expected": "",
                "description": "Empty input"
            },
            {
                "html": None,
                "expected": "",
                "description": "None input"
            },
            {
                "html": "<escaped> & \"quoted\"",
                "expected": "<escaped> & \"quoted\"",
                "description": "HTML entities (should remain as-is)"
            },
            {
                "html": "<ul><li>Item 1</li><li>Item 2</li></ul>",
                "expected": "Item 1 Item 2",
                "description": "List items"
            }
        ]
        
        passed = 0
        failed = 0
        results = []
        
        print(f"\nRunning {len(test_cases)} HTML cleaning test cases...\n")
        
        for i, test_case in enumerate(test_cases):
            print(f"Test Case {i+1}: {test_case['description']}")
            html_input = test_case['html']
            if html_input is None:
                print(f"Input: None")
            else:
                print(f"Input: {html_input[:100]}{'...' if len(str(html_input)) > 100 else ''}")
            
            try:
                cleaned = clean_html(test_case["html"])
                print(f"Output: {cleaned}")
                print(f"Expected: {test_case['expected']}")
                
                # Check if result matches expected
                test_passed = cleaned == test_case["expected"]
                
                if test_passed:
                    print(f"✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED")
                    failed += 1
                
                # Store detailed result
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "input": test_case["html"],
                    "output": cleaned,
                    "expected": test_case["expected"],
                    "passed": test_passed,
                    "type": "html_cleaning"
                })
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "input": test_case["html"],
                    "error": str(e),
                    "expected": test_case["expected"],
                    "passed": False,
                    "type": "html_cleaning"
                })
            
            print("-" * 80)
        
        # Print summary
        print(f"\n=== HTML CLEANING TEST SUMMARY ===")
        print(f"Total tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/len(test_cases)*100:.1f}%")
        
        return failed == 0, results
        
    except Exception as e:
        print(f"✗ Error testing HTML cleaning: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_keyword_matching():
    """Test keyword matching functionality"""
    print("\nTesting keyword matching functionality...")
    
    try:
        from sugar.backend.parsers.news_parser import contains_keywords
        
        # Test cases with expected results
        test_cases = [
            {
                "text": "This article contains sugar and commodity trading information",
                "keywords": ["sugar", "commodity"],
                "expected": True,
                "description": "Multiple keywords present"
            },
            {
                "text": "This article is about sugar and commodity prices",
                "keywords": ["sugar", "commodity"],
                "expected": True,
                "description": "Multiple keyword match"
            },
            {
                "text": "This article is about general market news",
                "keywords": ["sugar", "commodity"],
                "expected": False,
                "description": "No keywords present"
            },
            {
                "text": "Sugar futures are trading higher",
                "keywords": ["sugar"],
                "expected": True,
                "description": "Single keyword match"
            },
            {
                "text": "SUGAR in uppercase",
                "keywords": ["sugar"],
                "expected": True,
                "description": "Case insensitive match"
            },
            {
                "text": "Article about sugarcane production",
                "keywords": ["sugar"],
                "expected": False,
                "description": "Partial word match (should not match)"
            },
            {
                "text": "",
                "keywords": ["sugar"],
                "expected": False,
                "description": "Empty text"
            },
            {
                "text": "Valid content",
                "keywords": [],
                "expected": False,
                "description": "Empty keywords list"
            },
            {
                "text": None,
                "keywords": ["sugar"],
                "expected": False,
                "description": "None text input"
            },
            {
                "text": "Complex sugar commodity trading analysis",
                "keywords": ["sugar", "commodity", "trading", "analysis"],
                "expected": True,
                "description": "Multiple keyword matches"
            }
        ]
        
        passed = 0
        failed = 0
        results = []
        
        print(f"\nRunning {len(test_cases)} keyword matching test cases...\n")
        
        for i, test_case in enumerate(test_cases):
            print(f"Test Case {i+1}: {test_case['description']}")
            print(f"Text: {test_case['text']}")
            print(f"Keywords: {test_case['keywords']}")
            
            try:
                result = contains_keywords(test_case["text"], test_case["keywords"])
                print(f"Result: {result}")
                print(f"Expected: {test_case['expected']}")
                
                # Check if result matches expected
                test_passed = result == test_case["expected"]
                
                if test_passed:
                    print(f"✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED")
                    failed += 1
                
                # Store detailed result
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "text": test_case["text"],
                    "keywords": test_case["keywords"],
                    "result": result,
                    "expected": test_case["expected"],
                    "passed": test_passed,
                    "type": "keyword_matching"
                })
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "text": test_case["text"],
                    "keywords": test_case["keywords"],
                    "error": str(e),
                    "expected": test_case["expected"],
                    "passed": False,
                    "type": "keyword_matching"
                })
            
            print("-" * 80)
        
        # Print summary
        print(f"\n=== KEYWORD MATCHING TEST SUMMARY ===")
        print(f"Total tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/len(test_cases)*100:.1f}%")
        
        return failed == 0, results
        
    except Exception as e:
        print(f"✗ Error testing keyword matching: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_search_query_building():
    """Test search query building functionality"""
    print("\nTesting search query building functionality...")
    
    try:
        from sugar.backend.parsers.news_parser import build_search_query
        
        # Test cases with expected results
        test_cases = [
            {
                "topic_ids": ["20000373", "20000386"],
                "person_entities": None,
                "company_entities": None,
                "expected": "(topic:120000373) OR (topic:120000386)",
                "description": "Multiple topic IDs only"
            },
            {
                "topic_ids": ["20000373"],
                "person_entities": ["John Doe"],
                "company_entities": None,
                "expected": "(topic:120000373) AND (person:\"John Doe\")",
                "description": "Topic ID and person entity"
            },
            {
                "topic_ids": None,
                "person_entities": ["John Doe", "Jane Smith"],
                "company_entities": None,
                "expected": "(person:\"John Doe\") OR (person:\"Jane Smith\")",
                "description": "Multiple person entities"
            },
            {
                "topic_ids": ["20000373"],
                "person_entities": None,
                "company_entities": ["Apple Inc", "Google LLC"],
                "expected": "(topic:120000373) AND (company:\"Apple Inc\") AND (company:\"Google LLC\")",
                "description": "Topic ID and multiple company entities"
            },
            {
                "topic_ids": None,
                "person_entities": None,
                "company_entities": ["Microsoft Corp"],
                "expected": "(company:\"Microsoft Corp\")",
                "description": "Single company entity"
            },
            {
                "topic_ids": ["20000373", "20000386", "20000151"],
                "person_entities": ["Alan Greenspan"],
                "company_entities": ["Federal Reserve"],
                "expected": "(topic:120000373) OR (topic:120000386) OR (topic:120000151) AND (person:\"Alan Greenspan\") AND (company:\"Federal Reserve\")",
                "description": "Complex query with all parameters"
            },
            {
                "topic_ids": None,
                "person_entities": None,
                "company_entities": None,
                "expected": "",
                "description": "All parameters empty"
            },
            {
                "topic_ids": [],
                "person_entities": [],
                "company_entities": [],
                "expected": "",
                "description": "Empty lists"
            }
        ]
        
        passed = 0
        failed = 0
        results = []
        
        print(f"\nRunning {len(test_cases)} search query building test cases...\n")
        
        for i, test_case in enumerate(test_cases):
            print(f"Test Case {i+1}: {test_case['description']}")
            print(f"Topic IDs: {test_case['topic_ids']}")
            print(f"Person Entities: {test_case['person_entities']}")
            print(f"Company Entities: {test_case['company_entities']}")
            
            try:
                query = build_search_query(
                    test_case["topic_ids"], 
                    test_case["person_entities"], 
                    test_case["company_entities"]
                )
                print(f"Query: {query}")
                print(f"Expected: {test_case['expected']}")
                
                # Check if result matches expected
                test_passed = query == test_case["expected"]
                
                if test_passed:
                    print(f"✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED")
                    failed += 1
                
                # Store detailed result
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "topic_ids": test_case["topic_ids"],
                    "person_entities": test_case["person_entities"],
                    "company_entities": test_case["company_entities"],
                    "query": query,
                    "expected": test_case["expected"],
                    "passed": test_passed,
                    "type": "search_query_building"
                })
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "topic_ids": test_case["topic_ids"],
                    "person_entities": test_case["person_entities"],
                    "company_entities": test_case["company_entities"],
                    "error": str(e),
                    "expected": test_case["expected"],
                    "passed": False,
                    "type": "search_query_building"
                })
            
            print("-" * 80)
        
        # Print summary
        print(f"\n=== SEARCH QUERY BUILDING TEST SUMMARY ===")
        print(f"Total tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/len(test_cases)*100:.1f}%")
        
        return failed == 0, results
        
    except Exception as e:
        print(f"✗ Error testing search query building: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_article_id_generation():
    """Test article ID generation functionality"""
    print("\nTesting article ID generation functionality...")
    
    try:
        from sugar.backend.parsers.news_parser import generate_article_id
        
        # Test cases with expected results (should be consistent)
        test_cases = [
            {
                "url": "https://example.com/article1",
                "title": "Sugar Prices Rise",
                "published_date": "2024-01-15",
                "asset": "Sugar",
                "description": "Basic article ID generation"
            },
            {
                "url": "https://example.com/article1",
                "title": "Sugar Prices Rise",
                "published_date": "2024-01-15",
                "asset": "Oil",
                "description": "Different asset should produce different ID"
            },
            {
                "url": "https://example.com/article2",
                "title": "Sugar Prices Rise",
                "published_date": "2024-01-15",
                "asset": "Sugar",
                "description": "Different URL should produce different ID"
            },
            {
                "url": "https://example.com/article1",
                "title": "Different Title",
                "published_date": "2024-01-15",
                "asset": "Sugar",
                "description": "Different title should produce different ID"
            },
            {
                "url": "https://example.com/article1",
                "title": "Sugar Prices Rise",
                "published_date": "2024-01-16",
                "asset": "Sugar",
                "description": "Different date should produce different ID"
            },
            {
                "url": "",
                "title": "",
                "published_date": "",
                "asset": "",
                "description": "Empty inputs"
            },
            {
                "url": None,
                "title": None,
                "published_date": None,
                "asset": None,
                "description": "None inputs"
            },
            {
                "url": "https://example.com/article1",
                "title": "Sugar Prices Rise",
                "published_date": "2024-01-15",
                "asset": "Sugar",
                "description": "Consistency check (should match first case)"
            }
        ]
        
        passed = 0
        failed = 0
        results = []
        first_id = None
        
        print(f"\nRunning {len(test_cases)} article ID generation test cases...\n")
        
        for i, test_case in enumerate(test_cases):
            print(f"Test Case {i+1}: {test_case['description']}")
            print(f"URL: {test_case['url']}")
            print(f"Title: {test_case['title']}")
            print(f"Date: {test_case['published_date']}")
            print(f"Asset: {test_case['asset']}")
            
            try:
                article_id = generate_article_id(
                    test_case["url"],
                    test_case["title"],
                    test_case["published_date"],
                    test_case["asset"]
                )
                print(f"Generated ID: {article_id}")
                
                # Store first ID for consistency check
                if i == 0:
                    first_id = article_id
                
                # Validation checks
                test_passed = True
                
                # Check if ID is a valid MD5 hash (32 hex characters)
                if article_id:
                    test_passed = test_passed and len(article_id) == 32 and all(c in '0123456789abcdef' for c in article_id)
                
                # Consistency check for last test case
                if i == 7:  # Last test case
                    test_passed = test_passed and article_id == first_id
                
                # Uniqueness checks for different inputs
                if i == 1:  # Different asset
                    test_passed = test_passed and article_id != first_id
                elif i == 2:  # Different URL
                    test_passed = test_passed and article_id != first_id
                elif i == 3:  # Different title
                    test_passed = test_passed and article_id != first_id
                elif i == 4:  # Different date
                    test_passed = test_passed and article_id != first_id
                
                if test_passed:
                    print(f"✓ PASSED")
                    passed += 1
                else:
                    print(f"✗ FAILED")
                    failed += 1
                
                # Store detailed result
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "url": test_case["url"],
                    "title": test_case["title"],
                    "published_date": test_case["published_date"],
                    "asset": test_case["asset"],
                    "generated_id": article_id,
                    "first_id": first_id,
                    "passed": test_passed,
                    "type": "article_id_generation"
                })
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1
                results.append({
                    "test_case": i+1,
                    "description": test_case["description"],
                    "url": test_case["url"],
                    "title": test_case["title"],
                    "published_date": test_case["published_date"],
                    "asset": test_case["asset"],
                    "error": str(e),
                    "passed": False,
                    "type": "article_id_generation"
                })
            
            print("-" * 80)
        
        # Print summary
        print(f"\n=== ARTICLE ID GENERATION TEST SUMMARY ===")
        print(f"Total tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/len(test_cases)*100:.1f}%")
        
        return failed == 0, results
        
    except Exception as e:
        print(f"✗ Error testing article ID generation: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def main():
    """Main test function"""
    print("=== NEWS PARSING TEST SUITE ===")
    print(f"Started at: {datetime.now()}")
    
    # Run all tests
    html_passed, html_results = test_html_cleaning()
    keyword_passed, keyword_results = test_keyword_matching()
    query_passed, query_results = test_search_query_building()
    id_passed, id_results = test_article_id_generation()
    
    # Combine all results
    all_results = html_results + keyword_results + query_results + id_results
    
    # Overall result
    overall_passed = html_passed and keyword_passed and query_passed and id_passed
    
    print(f"\n=== OVERALL TEST RESULTS ===")
    print(f"HTML Cleaning Tests: {'PASSED' if html_passed else 'FAILED'}")
    print(f"Keyword Matching Tests: {'PASSED' if keyword_passed else 'FAILED'}")
    print(f"Search Query Building Tests: {'PASSED' if query_passed else 'FAILED'}")
    print(f"Article ID Generation Tests: {'PASSED' if id_passed else 'FAILED'}")
    print(f"Overall: {'PASSED' if overall_passed else 'FAILED'}")
    
    # Save detailed results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"news_parsing_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return 0 if overall_passed else 1

if __name__ == "__main__":
    exit(main())
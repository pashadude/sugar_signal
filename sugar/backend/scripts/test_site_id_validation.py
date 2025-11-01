#!/usr/bin/env python
"""
Test script to validate that the sugar source site IDs exist in the Opoint database.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.api.opoint.opoint_api import OpointAPI
from sugar.backend.parsers.sugar_news_fetcher import SUGAR_SOURCES_27

def test_site_ids():
    """Test that all sugar source site IDs exist in the Opoint database."""
    print("=== Testing Sugar Source Site IDs ===")
    
    # Get API key from environment
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("ERROR: OPOINT_API_KEY environment variable not found")
        return False
    
    # Initialize API
    api = OpointAPI(api_key=api_key)
    
    print(f"Testing {len(SUGAR_SOURCES_27)} sugar source site IDs...")
    
    valid_sites = []
    invalid_sites = []
    
    for source in SUGAR_SOURCES_27:
        source_name = source['name']
        source_id = source['id']
        
        print(f"\nTesting: {source_name} (ID: {source_id})")
        
        # First, try to search by site name
        site_response = api.search_site(source_name)
        
        if "error" in site_response:
            print(f"  ERROR: {site_response['error']}")
            invalid_sites.append((source_name, source_id, "API error"))
            continue
        
        sites = site_response.get("results", [])
        if not sites:
            print(f"  WARNING: No sites found matching '{source_name}'")
            invalid_sites.append((source_name, source_id, "No match found"))
            continue
        
        # Check if any of the returned sites have the expected ID
        found_matching_id = False
        for site in sites:
            returned_id = site.get("id")
            returned_name = site.get("name", "")
            
            print(f"  Found site: {returned_name} (ID: {returned_id})")
            
            # Check for exact ID match
            if returned_id == source_id:
                found_matching_id = True
                valid_sites.append((source_name, source_id))
                print(f"  ✅ MATCH: Found exact ID match")
                break
        
        if not found_matching_id:
            print(f"  ❌ NO MATCH: No site with expected ID {source_id}")
            invalid_sites.append((source_name, source_id, "ID mismatch"))
    
    # Print summary
    print(f"\n{'='*60}")
    print("SITE ID VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    print(f"Valid sites: {len(valid_sites)}")
    print(f"Invalid sites: {len(invalid_sites)}")
    
    if valid_sites:
        print(f"\n✅ Valid sites:")
        for name, id in valid_sites:
            print(f"  - {name} (ID: {id})")
    
    if invalid_sites:
        print(f"\n❌ Invalid sites:")
        for name, id, reason in invalid_sites:
            print(f"  - {name} (ID: {id}) - Reason: {reason}")
    
    return len(invalid_sites) == 0

def test_specific_site_id():
    """Test a specific site ID that was failing in the double filtering test."""
    print("\n=== Testing Specific Site ID ===")
    
    # Get API key from environment
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("ERROR: OPOINT_API_KEY environment variable not found")
        return False
    
    # Initialize API
    api = OpointAPI(api_key=api_key)
    
    # Test with Food Processing source that failed in the previous test
    test_source = SUGAR_SOURCES_27[0]  # Food Processing
    source_name = test_source['name']
    source_id = test_source['id']
    
    print(f"Testing: {source_name} (ID: {source_id})")
    
    # Search for the site by name
    site_response = api.search_site(source_name)
    
    if "error" in site_response:
        print(f"ERROR: {site_response['error']}")
        return False
    
    sites = site_response.get("results", [])
    if not sites:
        print(f"WARNING: No sites found matching '{source_name}'")
        return False
    
    print(f"Found {len(sites)} sites matching '{source_name}':")
    for i, site in enumerate(sites):
        print(f"  {i+1}. {site.get('name', 'Unknown')} (ID: {site.get('id', 'Unknown')})")
    
    # Check if we have an exact match
    exact_match = None
    for site in sites:
        if site.get("id") == source_id:
            exact_match = site
            break
    
    if exact_match:
        print(f"\n✅ Found exact match: {exact_match.get('name')} (ID: {exact_match.get('id')})")
        return True
    else:
        print(f"\n❌ No exact match found for ID {source_id}")
        
        # Find the closest match by name
        best_match = None
        best_similarity = 0
        
        for site in sites:
            site_name_in_db = site.get('name', '').lower()
            source_name_lower = source_name.lower()
            
            # Simple similarity check
            if site_name_in_db == source_name_lower:
                similarity = 1.0
            elif source_name_lower in site_name_in_db or site_name_in_db in source_name_lower:
                similarity = 0.8
            else:
                similarity = 0.0
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = site
        
        if best_match and best_similarity > 0.5:
            print(f"Closest match: {best_match.get('name')} (ID: {best_match.get('id')})")
            print(f"Consider updating the source ID from {source_id} to {best_match.get('id')}")
        
        return False

def main():
    """Run all site ID validation tests."""
    print("Starting site ID validation tests...\n")
    
    # Test specific site ID first
    specific_test_passed = test_specific_site_id()
    
    # Test all site IDs
    all_test_passed = test_site_ids()
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    
    if specific_test_passed:
        print("✅ Specific site ID test passed")
    else:
        print("❌ Specific site ID test failed")
    
    if all_test_passed:
        print("✅ All site IDs test passed")
    else:
        print("❌ All site IDs test failed")
    
    overall_success = specific_test_passed and all_test_passed
    
    if overall_success:
        print("\n🎉 All site ID validation tests passed!")
    else:
        print(f"\n⚠️  Some site ID validation tests failed.")
        print("This may explain why double filtering is not working correctly.")
        print("Please verify that the site IDs in SUGAR_SOURCES_27 are correct.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
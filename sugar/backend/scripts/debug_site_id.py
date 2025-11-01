#!/usr/bin/env python
"""
Debug script to check specific site ID comparisons.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.api.opoint.opoint_api import OpointAPI

def debug_site_id(source_name, expected_id):
    """Debug a specific site ID comparison."""
    print(f"\n=== Debugging: {source_name} (Expected ID: {expected_id}) ===")
    
    # Get API key from environment
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("ERROR: OPOINT_API_KEY environment variable not found")
        return False
    
    # Initialize API
    api = OpointAPI(api_key=api_key)
    
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
    
    found_match = False
    for i, site in enumerate(sites):
        returned_id = site.get("id")
        returned_name = site.get("name", "")
        
        print(f"  {i+1}. {returned_name} (ID: {returned_id})")
        
        # Debug the ID comparison
        print(f"     Comparing: {returned_id} == {expected_id} -> {returned_id == expected_id}")
        print(f"     Types: returned_id={type(returned_id)}, expected_id={type(expected_id)}")
        
        if returned_id == expected_id:
            print(f"     ✅ MATCH FOUND!")
            found_match = True
        else:
            # Try converting to string for comparison
            if str(returned_id) == str(expected_id):
                print(f"     ✅ STRING MATCH FOUND!")
                found_match = True
    
    return found_match

def main():
    """Debug specific site IDs."""
    print("Starting site ID debugging...\n")
    
    # Test a few specific sources that should have matches
    test_sources = [
        ("Sugar Producer", 124631),
        ("Argus Media", 82120),
        ("Fastmarkets", 30542),
        ("Agriinsite", 449222),
        ("Tridge", 448815),
        ("Food Navigator USA", 26214),
        ("USDA", 15086),
    ]
    
    results = []
    for source_name, expected_id in test_sources:
        match_found = debug_site_id(source_name, expected_id)
        results.append((source_name, expected_id, match_found))
    
    # Print summary
    print(f"\n{'='*60}")
    print("DEBUG SUMMARY")
    print(f"{'='*60}")
    
    matches = 0
    for source_name, expected_id, match_found in results:
        status = "✅ MATCH" if match_found else "❌ NO MATCH"
        print(f"{status}: {source_name} (ID: {expected_id})")
        if match_found:
            matches += 1
    
    print(f"\nTotal matches: {matches}/{len(results)}")
    
    if matches == len(results):
        print("\n🎉 All tested sources have correct IDs!")
    else:
        print(f"\n⚠️  {len(results) - matches} sources have ID issues.")
    
    return matches == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
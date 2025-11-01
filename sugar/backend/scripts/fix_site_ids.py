#!/usr/bin/env python
"""
Script to fix the incorrect site IDs in SUGAR_SOURCES_27 configuration.
This script extracts the correct IDs from the Opoint API and updates the configuration.
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

def get_correct_site_id(source_name):
    """
    Get the correct site ID for a given source name from the Opoint API.
    Returns the first matching site ID.
    """
    # Get API key from environment
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("ERROR: OPOINT_API_KEY environment variable not found")
        return None
    
    # Initialize API
    api = OpointAPI(api_key=api_key)
    
    # Search for the site by name
    site_response = api.search_site(source_name)
    
    if "error" in site_response:
        print(f"ERROR searching for {source_name}: {site_response['error']}")
        return None
    
    sites = site_response.get("results", [])
    if not sites:
        print(f"WARNING: No sites found matching '{source_name}'")
        return None
    
    # Return the ID of the first exact match
    for site in sites:
        site_name_in_db = site.get("name", "")
        if site_name_in_db.lower() == source_name.lower():
            return site.get("id")
    
    # If no exact match, return the ID of the first result
    first_site = sites[0]
    print(f"WARNING: No exact match for '{source_name}', using first result: {first_site.get('name')}")
    return first_site.get("id")

def main():
    """Fix the site IDs in SUGAR_SOURCES_27 configuration."""
    print("=== Fixing Site IDs in SUGAR_SOURCES_27 ===\n")
    
    corrected_sources = []
    
    for source in SUGAR_SOURCES_27:
        source_name = source['name']
        old_id = source['id']
        
        print(f"Processing: {source_name} (old ID: {old_id})")
        
        # Get the correct site ID
        correct_id = get_correct_site_id(source_name)
        
        if correct_id:
            print(f"  ✅ Correct ID: {correct_id}")
            corrected_sources.append({
                'name': source_name,
                'id': correct_id
            })
        else:
            print(f"  ❌ Could not find correct ID, keeping old ID: {old_id}")
            corrected_sources.append({
                'name': source_name,
                'id': old_id
            })
        
        print()
    
    # Print the corrected configuration
    print("=== Corrected SUGAR_SOURCES_27 Configuration ===")
    print("SUGAR_SOURCES_27 = [")
    
    for source in corrected_sources:
        print(f"    {{'name': '{source['name']}', 'id': {source['id']}}},")
    
    print("]")
    
    # Print Python code to update the configuration
    print("\n=== Python Code to Update Configuration ===")
    print("# Copy this code to sugar_news_fetcher.py to update SUGAR_SOURCES_27")
    print("SUGAR_SOURCES_27 = [")
    
    for source in corrected_sources:
        print(f"    {{'name': '{source['name']}', 'id': {source['id']}}},")
    
    print("]")
    
    return corrected_sources

if __name__ == "__main__":
    corrected_sources = main()
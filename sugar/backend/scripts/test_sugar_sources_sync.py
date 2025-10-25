#!/usr/bin/env python
"""
Test script to verify that sugar sources are synchronized between 
sugar_news_fetcher.py and source_filter.py
"""

import sys
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import SUGAR_SOURCES, ALL_SUGAR_SOURCE_NAMES
from sugar.backend.parsers.source_filter import get_sugar_trusted_sources, get_sugar_trusted_source_ids

def test_source_synchronization():
    """Test that sources are synchronized between the two files"""
    print("=== Testing Sugar Sources Synchronization ===\n")
    
    # Get sources from both files
    fetcher_sources = set(ALL_SUGAR_SOURCE_NAMES)
    filter_sources = get_sugar_trusted_sources()
    
    print(f"Sources in sugar_news_fetcher.py: {len(fetcher_sources)}")
    print(f"Sources in source_filter.py: {len(filter_sources)}")
    
    # Check for missing sources in filter
    missing_in_filter = fetcher_sources - filter_sources
    if missing_in_filter:
        print(f"\n❌ Sources missing in source_filter.py: {missing_in_filter}")
    else:
        print("\n✅ All sources from sugar_news_fetcher.py are present in source_filter.py")
    
    # Check for extra sources in filter
    extra_in_filter = filter_sources - fetcher_sources
    if extra_in_filter:
        print(f"\n⚠️  Extra sources in source_filter.py: {extra_in_filter}")
    else:
        print("\n✅ No extra sources in source_filter.py")
    
    # Test source IDs
    print("\n=== Testing Source IDs ===\n")
    
    # Extract source IDs from SUGAR_SOURCES
    fetcher_source_ids = set()
    for category, sources in SUGAR_SOURCES.items():
        if isinstance(sources, dict):
            for region, region_sources in sources.items():
                fetcher_source_ids.update(source['id'] for source in region_sources)
        else:
            fetcher_source_ids.update(source['id'] for source in sources)
    
    filter_source_ids = get_sugar_trusted_source_ids()
    
    print(f"Source IDs in sugar_news_fetcher.py: {len(fetcher_source_ids)}")
    print(f"Source IDs in source_filter.py: {len(filter_source_ids)}")
    
    # Check for missing IDs in filter
    missing_ids_in_filter = fetcher_source_ids - filter_source_ids
    if missing_ids_in_filter:
        print(f"\n❌ Source IDs missing in source_filter.py: {missing_ids_in_filter}")
    else:
        print("\n✅ All source IDs from sugar_news_fetcher.py are present in source_filter.py")
    
    # Check for extra IDs in filter
    extra_ids_in_filter = filter_source_ids - fetcher_source_ids
    if extra_ids_in_filter:
        print(f"\n⚠️  Extra source IDs in source_filter.py: {extra_ids_in_filter}")
    else:
        print("\n✅ No extra source IDs in source_filter.py")
    
    # Test specific new sources
    print("\n=== Testing New Sources ===\n")
    
    new_sources = [
        {'name': "Barron's", 'id': 28875},
        {'name': 'Trading Economics', 'id': 213991},
        {'name': 'Chini Mandi', 'id': 442001},
        {'name': 'Globy', 'id': 464928},
        {'name': 'CME Group', 'id': 2737765}
    ]
    
    all_new_sources_present = True
    for source in new_sources:
        name_in_fetcher = source['name'] in fetcher_sources
        name_in_filter = source['name'] in filter_sources
        id_in_fetcher = source['id'] in fetcher_source_ids
        id_in_filter = source['id'] in filter_source_ids
        
        status = "✅" if all([name_in_fetcher, name_in_filter, id_in_fetcher, id_in_filter]) else "❌"
        print(f"{status} {source['name']} (ID: {source['id']})")
        print(f"   - Name in fetcher: {name_in_fetcher}")
        print(f"   - Name in filter: {name_in_filter}")
        print(f"   - ID in fetcher: {id_in_fetcher}")
        print(f"   - ID in filter: {id_in_filter}")
        
        if not all([name_in_fetcher, name_in_filter, id_in_fetcher, id_in_filter]):
            all_new_sources_present = False
    
    # Overall result
    print("\n=== Overall Result ===\n")
    if (not missing_in_filter and not extra_in_filter and 
        not missing_ids_in_filter and not extra_ids_in_filter and 
        all_new_sources_present):
        print("✅ All tests passed! Sources are properly synchronized.")
        return True
    else:
        print("❌ Some tests failed. Sources are not properly synchronized.")
        return False

if __name__ == "__main__":
    success = test_source_synchronization()
    sys.exit(0 if success else 1)
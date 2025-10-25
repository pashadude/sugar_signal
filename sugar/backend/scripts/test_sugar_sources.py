#!/usr/bin/env python
"""
Test script to verify that sugar-specific sources are properly configured
and integrated with the news fetching pipeline.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import SUGAR_SOURCES, ALL_SUGAR_SOURCES, ALL_SUGAR_SOURCE_NAMES, MEDIA_TOPIC_IDS
from sugar.backend.parsers.source_filter import get_sugar_trusted_sources, get_sugar_trusted_source_ids, is_trusted_source
from sugar.backend.parsers.news_parser import build_search_query

def test_sugar_sources_configuration():
    """Test that sugar sources are properly configured"""
    print("=== Testing Sugar Sources Configuration ===")
    
    # Test SUGAR_SOURCES structure
    print(f"Number of source categories: {len(SUGAR_SOURCES)}")
    
    total_sources = 0
    total_source_names = 0
    for category, sources in SUGAR_SOURCES.items():
        if isinstance(sources, dict):
            # Regional sources
            for region, region_sources in sources.items():
                print(f"  {category}.{region}: {len(region_sources)} sources")
                total_sources += len(region_sources)
                total_source_names += len([s['name'] for s in region_sources])
        else:
            # Flat source lists
            print(f"  {category}: {len(sources)} sources")
            total_sources += len(sources)
            total_source_names += len([s['name'] for s in sources])
    
    print(f"Total sources in SUGAR_SOURCES: {total_sources}")
    print(f"Length of ALL_SUGAR_SOURCES: {len(ALL_SUGAR_SOURCES)}")
    print(f"Length of ALL_SUGAR_SOURCE_NAMES: {len(ALL_SUGAR_SOURCE_NAMES)}")
    
    # Verify consistency
    assert total_sources == len(ALL_SUGAR_SOURCES), "Mismatch in source counts"
    assert total_source_names == len(ALL_SUGAR_SOURCE_NAMES), "Mismatch in source name counts"
    print("✓ Source counts are consistent")
    
    # Test that all sources are unique
    assert len(ALL_SUGAR_SOURCES) == len(set(str(s) for s in ALL_SUGAR_SOURCES)), "Duplicate sources found"
    print("✓ All sources are unique")
    
    # Test that all source names are unique
    assert len(ALL_SUGAR_SOURCE_NAMES) == len(set(ALL_SUGAR_SOURCE_NAMES)), "Duplicate source names found"
    print("✓ All source names are unique")
    
    return True

def test_source_filtering():
    """Test that sugar sources are properly integrated with source filtering"""
    print("\n=== Testing Source Filtering Integration ===")
    
    # Test get_sugar_trusted_sources
    sugar_trusted = get_sugar_trusted_sources()
    print(f"Number of sugar trusted sources: {len(sugar_trusted)}")
    
    # Test get_sugar_trusted_source_ids
    sugar_trusted_ids = get_sugar_trusted_source_ids()
    print(f"Number of sugar trusted source IDs: {len(sugar_trusted_ids)}")
    
    # Verify that the number of names and IDs match
    assert len(sugar_trusted) == len(sugar_trusted_ids), "Mismatch between source names and IDs count"
    print("✓ Source names and IDs counts match")
    
    # Test that all sugar sources are in trusted sources (by name)
    for source in ALL_SUGAR_SOURCES:
        assert is_trusted_source(source['name']), f"Source '{source['name']}' is not trusted"
    print("✓ All sugar sources are trusted by name")
    
    # Test that all sugar sources are in trusted sources (by ID)
    for source in ALL_SUGAR_SOURCES:
        assert is_trusted_source(None, source['id']), f"Source ID '{source['id']}' is not trusted"
    print("✓ All sugar sources are trusted by ID")
    
    # Test that non-sugar sources work as before
    assert is_trusted_source("Reuters"), "Generic trusted source should be trusted"
    assert not is_trusted_source("Guelph Today"), "Non-trusted source should not be trusted"
    print("✓ Generic source filtering still works")
    
    # Test ID-based filtering takes precedence
    # Create a fake source with a trusted ID but untrusted name
    assert is_trusted_source("Untrusted Name", 171463), "ID-based filtering should take precedence"
    print("✓ ID-based filtering takes precedence over name-based filtering")
    
    return True

def test_search_query_building():
    """Test that sugar sources are properly integrated with search query building"""
    print("\n=== Testing Search Query Building ===")
    
    # Test without sugar sources
    query_without_sources = build_search_query(
        topic_ids=['20000373'],
        person_entities=['John Doe'],
        company_entities=['Cargill']
    )
    print(f"Query without sugar sources: {query_without_sources}")
    
    # Test with sugar sources
    query_with_sources = build_search_query(
        topic_ids=['20000373'],
        person_entities=['John Doe'],
        company_entities=['Cargill'],
        sugar_sources=['Sugar Online', 'Reuters Commodities']
    )
    print(f"Query with sugar sources: {query_with_sources}")
    
    # Verify that sugar sources are included
    assert 'source:"Sugar Online"' in query_with_sources, "Sugar source not in query"
    assert 'source:"Reuters Commodities"' in query_with_sources, "Sugar source not in query"
    print("✓ Sugar sources are properly included in search queries")
    
    return True

def test_media_topic_ids():
    """Test that media topic IDs are properly configured"""
    print("\n=== Testing Media Topic IDs ===")
    
    print(f"Number of media topic IDs: {len(MEDIA_TOPIC_IDS)}")
    print(f"Media topic IDs: {MEDIA_TOPIC_IDS}")
    
    # Verify that topic IDs are strings
    for topic_id in MEDIA_TOPIC_IDS:
        assert isinstance(topic_id, str), f"Topic ID '{topic_id}' is not a string"
    print("✓ All media topic IDs are strings")
    
    return True

def main():
    """Run all tests"""
    print("Testing sugar-specific sources integration...")
    
    try:
        test_sugar_sources_configuration()
        test_source_filtering()
        test_search_query_building()
        test_media_topic_ids()
        
        print("\n=== All Tests Passed! ===")
        print("Sugar-specific sources have been successfully integrated with the news fetching pipeline.")
        
        return True
        
    except Exception as e:
        print(f"\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
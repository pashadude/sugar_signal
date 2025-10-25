#!/usr/bin/env python
"""
Test script for weekly date range generation and dynamic quota allocation
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import (
    generate_date_ranges,
    calculate_source_quotas,
    get_source_category,
    SOURCE_CATEGORY_WEIGHTS,
    SOURCE_RELIABILITY_SCORES,
    SUGAR_SOURCES
)

def test_weekly_date_ranges():
    """Test the weekly date range generation function"""
    print("=== Testing Weekly Date Range Generation ===")
    
    # Test with 4 weeks (1 month)
    date_ranges = generate_date_ranges(weeks_back=4)
    
    print(f"Generated {len(date_ranges)} weekly date ranges:")
    for i, (start_date, end_date) in enumerate(date_ranges):
        print(f"  Week {i+1}: {start_date.date()} to {end_date.date()}")
        # Verify that each range is exactly 7 days
        duration = end_date - start_date
        expected_duration = timedelta(days=6, hours=23, minutes=59, seconds=59)
        if duration == expected_duration:
            print(f"    ✓ Duration correct: {duration}")
        else:
            print(f"    ✗ Duration incorrect: {duration} (expected: {expected_duration})")
    
    # Test chronological order
    for i in range(1, len(date_ranges)):
        if date_ranges[i][0] > date_ranges[i-1][0]:
            print(f"  ✓ Week {i+1} is after week {i}")
        else:
            print(f"  ✗ Week {i+1} is not after week {i}")
    
    print()

def test_dynamic_quota_allocation():
    """Test the dynamic quota allocation function"""
    print("=== Testing Dynamic Quota Allocation ===")
    
    # Test with a small max_articles value
    max_articles = 100
    quotas = calculate_source_quotas(max_articles, SUGAR_SOURCES)
    
    print(f"Allocating {max_articles} articles among {len(quotas)} sources:")
    
    total_allocated = 0
    for source, quota in quotas.items():
        category = get_source_category(source, SUGAR_SOURCES)
        reliability = SOURCE_RELIABILITY_SCORES.get(source, 0.5)
        category_weight = SOURCE_CATEGORY_WEIGHTS.get(category, 0.5)
        expected_weight = category_weight * reliability
        
        print(f"  - {source} ({category}): {quota} articles (weight: {expected_weight:.2f})")
        total_allocated += quota
    
    print(f"\nTotal allocated: {total_allocated} articles")
    
    # Verify that we didn't exceed max_articles
    if total_allocated <= max_articles:
        print(f"✓ Total allocation ({total_allocated}) <= max_articles ({max_articles})")
    else:
        print(f"✗ Total allocation ({total_allocated}) > max_articles ({max_articles})")
    
    # Verify that each source got at least 1 article
    min_quota = min(quotas.values())
    if min_quota >= 1:
        print(f"✓ Minimum quota per source: {min_quota}")
    else:
        print(f"✗ Minimum quota per source: {min_quota} (should be >= 1)")
    
    # Test with a very small max_articles value
    print("\nTesting with very small max_articles (10):")
    small_quotas = calculate_source_quotas(10, SUGAR_SOURCES)
    small_total = sum(small_quotas.values())
    print(f"Total allocated: {small_total} articles")
    
    if small_total <= 10:
        print("✓ Allocation respects max_articles limit")
    else:
        print("✗ Allocation exceeds max_articles limit")
    
    print()

def test_source_category_weights():
    """Test source category weights and reliability scores"""
    print("=== Testing Source Category Weights and Reliability Scores ===")
    
    print("Source category weights:")
    for category, weight in SOURCE_CATEGORY_WEIGHTS.items():
        print(f"  - {category}: {weight}")
    
    print("\nTop 5 sources by reliability score:")
    sorted_sources = sorted(SOURCE_RELIABILITY_SCORES.items(), key=lambda x: x[1], reverse=True)[:5]
    for source, reliability in sorted_sources:
        category = get_source_category(source, SUGAR_SOURCES)
        print(f"  - {source} ({category}): {reliability:.2f}")
    
    print("\nBottom 5 sources by reliability score:")
    sorted_sources = sorted(SOURCE_RELIABILITY_SCORES.items(), key=lambda x: x[1])[:5]
    for source, reliability in sorted_sources:
        category = get_source_category(source, SUGAR_SOURCES)
        print(f"  - {source} ({category}): {reliability:.2f}")
    
    print()

def test_quota_distribution():
    """Test that quota distribution follows expected patterns"""
    print("=== Testing Quota Distribution Patterns ===")
    
    max_articles = 200
    quotas = calculate_source_quotas(max_articles, SUGAR_SOURCES)
    
    # Group quotas by category
    category_quotas = {}
    for source, quota in quotas.items():
        category = get_source_category(source, SUGAR_SOURCES)
        if category not in category_quotas:
            category_quotas[category] = []
        category_quotas[category].append(quota)
    
    print("Quota distribution by category:")
    for category, quota_list in category_quotas.items():
        category_total = sum(quota_list)
        category_avg = category_total / len(quota_list)
        category_weight = SOURCE_CATEGORY_WEIGHTS.get(category, 0.5)
        print(f"  - {category} (weight: {category_weight}):")
        print(f"    Total: {category_total}, Average: {category_avg:.1f}, Sources: {len(quota_list)}")
    
    # Verify that higher weight categories get more quota on average
    category_avgs = {cat: sum(quotas)/len(quotas) for cat, quotas in category_quotas.items()}
    sorted_cats = sorted(category_avgs.items(), key=lambda x: x[1], reverse=True)
    
    print("\nCategories by average quota per source:")
    for category, avg_quota in sorted_cats:
        weight = SOURCE_CATEGORY_WEIGHTS.get(category, 0.5)
        print(f"  - {category} (weight: {weight}): {avg_quota:.1f} avg quota")
    
    print()

def main():
    """Run all tests"""
    print("Testing Weekly Date Ranges and Dynamic Quota Allocation")
    print("=" * 60)
    
    test_weekly_date_ranges()
    test_dynamic_quota_allocation()
    test_source_category_weights()
    test_quota_distribution()
    
    print("All tests completed!")

if __name__ == "__main__":
    main()
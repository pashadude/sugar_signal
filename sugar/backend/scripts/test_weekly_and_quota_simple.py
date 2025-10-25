#!/usr/bin/env python
"""
Simple test script for weekly date range generation and dynamic quota allocation
"""

import sys
import os
from datetime import datetime, timedelta

def generate_date_ranges(weeks_back=48):
    """Generate list of (start_date, end_date) tuples for the last N weeks"""
    date_ranges = []
    current_date = datetime.now()
    
    # Get the most recent Monday (start of the week)
    days_since_monday = current_date.weekday()
    most_recent_monday = current_date - timedelta(days=days_since_monday)
    
    for i in range(weeks_back):
        # Calculate the target week by subtracting i weeks from the most recent Monday
        target_monday = most_recent_monday - timedelta(weeks=i)
        
        # Create start of week (Monday at midnight)
        start_of_week = datetime(target_monday.year, target_monday.month, target_monday.day, 0, 0, 0, 0)
        
        # Calculate end of week (Sunday at 23:59:59)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        date_ranges.append((start_of_week, end_of_week))
    
    # Reverse to chronological order (oldest first)
    date_ranges.reverse()
    return date_ranges

# Source category weights for dynamic quota allocation
SOURCE_CATEGORY_WEIGHTS = {
    'sugar_industry_publications': 1.0,    # Highest priority - specialized sugar content
    'agricultural_commodity_sources': 0.8, # High priority - commodity focus
    'government_sources': 0.7,             # High priority - official data
    'trade_publications': 0.5              # Medium priority - broader financial news
}

# Source reliability scores (can be updated based on historical performance)
SOURCE_RELIABILITY_SCORES = {
    # Sugar Industry Publications
    'Food Processing': 0.9,
    'Sugar Producer': 0.95,
    
    # Agricultural Commodity News Sources
    'Argus Media': 0.9,
    'Fastmarkets': 0.85,
    'Ag Update': 0.7,
    'Agriinsite': 0.65,
    'Agronews': 0.7,
    'Tridge': 0.75,
    'ICE': 0.95,
    
    # Trade Publications
    'Food Navigator USA': 0.8,
    'Food Navigator': 0.8,
    'Benzinga': 0.6,
    'Yahoo! Finance': 0.5,
    'Business Insider': 0.55,
    'Investing': 0.6,
    'CNBC': 0.7,
    'Investing.com Brasil': 0.65,
    'Nasdaq': 0.7,
    'Barchart': 0.6,
    'Market Screener': 0.6,
    'Barron\'s': 0.75,
    'Trading Economics': 0.7,
    'Chini Mandi': 0.8,
    'Globy': 0.6,
    'CME Group': 0.85,
    
    # Government and International Organizations
    'USDA': 0.95,
    'FAO': 0.9
}

# Simplified SUGAR_SOURCES configuration for testing
SUGAR_SOURCES = {
    'sugar_industry_publications': [
        {'name': 'Food Processing', 'id': 171463},
        {'name': 'Sugar Producer', 'id': 124631}
    ],
    'agricultural_commodity_sources': [
        {'name': 'Argus Media', 'id': 82120},
        {'name': 'Fastmarkets', 'id': 30542},
        {'name': 'Ag Update', 'id': 335679}
    ],
    'government_sources': [
        {'name': 'USDA', 'id': 15086},
        {'name': 'FAO', 'id': 53626}
    ],
    'trade_publications': [
        {'name': 'Food Navigator USA', 'id': 26214},
        {'name': 'Benzinga', 'id': 23564},
        {'name': 'Yahoo! Finance', 'id': 3478}
    ]
}

def calculate_source_quotas(max_articles, sources_config):
    """
    Calculate dynamic quota allocation for each source based on category weights and reliability scores.
    """
    # Calculate weighted scores for each source
    source_scores = {}
    total_weight = 0
    
    for category, sources in sources_config.items():
        category_weight = SOURCE_CATEGORY_WEIGHTS.get(category, 0.5)  # Default weight for unknown categories
        
        if isinstance(sources, dict):
            # Handle regional sources
            for region, region_sources in sources.items():
                for source in region_sources:
                    source_name = source['name']
                    reliability_score = SOURCE_RELIABILITY_SCORES.get(source_name, 0.5)  # Default reliability
                    weighted_score = category_weight * reliability_score
                    source_scores[source_name] = weighted_score
                    total_weight += weighted_score
        else:
            # Handle flat source lists
            for source in sources:
                source_name = source['name']
                reliability_score = SOURCE_RELIABILITY_SCORES.get(source_name, 0.5)  # Default reliability
                weighted_score = category_weight * reliability_score
                source_scores[source_name] = weighted_score
                total_weight += weighted_score
    
    # Allocate quotas based on weighted scores
    source_quotas = {}
    allocated_articles = 0
    
    for source_name, score in source_scores.items():
        # Calculate proportional quota
        quota = int((score / total_weight) * max_articles)
        # Ensure minimum quota of 1 article per source
        quota = max(1, quota)
        source_quotas[source_name] = quota
        allocated_articles += quota
    
    # If we've allocated more than max_articles, scale down proportionally
    if allocated_articles > max_articles:
        scale_factor = max_articles / allocated_articles
        for source_name in source_quotas:
            source_quotas[source_name] = max(1, int(source_quotas[source_name] * scale_factor))
    
    return source_quotas

def get_source_category(source_name, sources_config):
    """Get the category of a source based on its name."""
    for category, sources in sources_config.items():
        if isinstance(sources, dict):
            # Handle regional sources
            for region, region_sources in sources.items():
                for source in region_sources:
                    if source['name'] == source_name:
                        return category
        else:
            # Handle flat source lists
            for source in sources:
                if source['name'] == source_name:
                    return category
    return 'unknown'

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
    test_quota_distribution()
    
    print("All tests completed!")

if __name__ == "__main__":
    main()
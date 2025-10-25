#!/usr/bin/env python3
"""
Sugar Triage Filters Summary Script

This script generates a readable summary of all triage filters used in the sugar news pipeline.
It extracts and formats the filter criteria from sugar_triage_filter.py for easy reference.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any

def extract_filter_data():
    """Extract filter data from sugar_triage_filter.py"""
    
    # Read the sugar_triage_filter.py file
    filter_file = Path("ShinkaEvolve/shinka/examples/sugar/backend/text_filtering/sugar_triage_filter.py")
    
    if not filter_file.exists():
        print(f"Error: Could not find {filter_file}")
        return None
    
    with open(filter_file, 'r') as f:
        content = f.read()
    
    # Extract exclusion keywords
    exclusion_match = re.search(r'EXCLUSION_KEYWORDS = \[(.*?)\]', content, re.DOTALL)
    exclusion_keywords = []
    if exclusion_match:
        exclusion_text = exclusion_match.group(1)
        # Extract quoted strings
        exclusion_keywords = re.findall(r'"([^"]*)"', exclusion_text)
    
    # Extract main keywords
    keywords_match = re.search(r'KEYWORDS = \{(.*?)\}', content, re.DOTALL)
    keywords_dict = {}
    if keywords_match:
        keywords_text = keywords_match.group(1)
        # Extract each category
        categories = re.findall(r'"(\w+)":\s*\[(.*?)\]', keywords_text, re.DOTALL)
        for category, category_text in categories:
            category_keywords = re.findall(r'"([^"]*)"', category_text)
            keywords_dict[category] = category_keywords
    
    # Extract structured patterns
    structured_patterns = []
    pattern_matches = re.findall(r're\.compile\(r"(.*?)"', content)
    for pattern in pattern_matches:
        if any(char in pattern for char in ['\\*', '\\|', '\\d', 'Contract', 'Date', 'Price']):
            structured_patterns.append(pattern)
    
    return {
        'exclusion_keywords': exclusion_keywords,
        'keywords_dict': keywords_dict,
        'structured_patterns': structured_patterns
    }

def print_filter_summary():
    """Print a formatted summary of all filters"""
    
    print("=" * 80)
    print("SUGAR NEWS PIPELINE - TRIAGE FILTERS SUMMARY")
    print("=" * 80)
    print()
    
    filter_data = extract_filter_data()
    if not filter_data:
        return
    
    # 1. Filter Overview
    print("1. FILTER OVERVIEW")
    print("-" * 40)
    print("The sugar news pipeline uses a multi-layered filtering approach:")
    print("   a) Quality Control Filters")
    print("   b) Main Keyword Filter")
    print("   c) Exclusion Filter")
    print("   d) Secondary Filter (Event + Agriculture)")
    print("   e) Context Zone Filters")
    print("   f) Structured Data Filter")
    print()
    
    # 2. Quality Control Filters
    print("2. QUALITY CONTROL FILTERS")
    print("-" * 40)
    print("   • Media Topic Check: IPTC MediaTopic pre-filtering")
    print("   • Text Validation: Non-empty string check")
    print("   • Minimum Length: 20 characters")
    print("   • Maximum Length: Configurable (if set)")
    print()
    
    # 3. Main Keywords
    print("3. MAIN KEYWORDS (Primary Sugar Terms)")
    print("-" * 40)
    if 'main' in filter_data['keywords_dict']:
        main_keywords = filter_data['keywords_dict']['main']
        for i, keyword in enumerate(main_keywords, 1):
            print(f"   {i:2d}. {keyword}")
    print()
    
    # 4. Exclusion Keywords
    print("4. EXCLUSION KEYWORDS (Non-Sugar Commodities)")
    print("-" * 40)
    exclusion_keywords = filter_data['exclusion_keywords']
    for i, keyword in enumerate(exclusion_keywords, 1):
        print(f"   {i:2d}. {keyword}")
    print()
    
    # 5. Context Zone Keywords
    print("5. CONTEXT ZONE KEYWORDS")
    print("-" * 40)
    
    # Market Zone
    print("   a) MARKET ZONE")
    print("      Purpose: Market dynamics, trade, and economic aspects")
    if 'market' in filter_data['keywords_dict']:
        market_keywords = filter_data['keywords_dict']['market']
        for i, keyword in enumerate(market_keywords, 1):
            print(f"      {i:2d}. {keyword}")
    print()
    
    # Supply Chain Zone
    print("   b) SUPPLY CHAIN ZONE")
    print("      Purpose: Production, processing, and logistics")
    if 'supply_chain' in filter_data['keywords_dict']:
        supply_keywords = filter_data['keywords_dict']['supply_chain']
        for i, keyword in enumerate(supply_keywords, 1):
            print(f"      {i:2d}. {keyword}")
    print()
    
    # Event Zone
    print("   c) EVENT ZONE")
    print("      Purpose: Events impacting sugar production/markets")
    if 'event' in filter_data['keywords_dict']:
        event_keywords = filter_data['keywords_dict']['event']
        for i, keyword in enumerate(event_keywords, 1):
            print(f"      {i:2d}. {keyword}")
    print()
    
    # Region Zone
    print("   d) REGION ZONE")
    print("      Purpose: Key sugar-producing regions and organizations")
    if 'region' in filter_data['keywords_dict']:
        region_keywords = filter_data['keywords_dict']['region']
        for i, keyword in enumerate(region_keywords, 1):
            print(f"      {i:2d}. {keyword}")
    print()
    
    # 6. Structured Data Patterns
    print("6. STRUCTURED DATA PATTERNS")
    print("-" * 40)
    print("   Purpose: Extract pricing and market data from structured formats")
    print("   Patterns:")
    for i, pattern in enumerate(filter_data['structured_patterns'], 1):
        print(f"   {i}. {pattern}")
    print()
    
    # 7. Filter Logic
    print("7. FILTER LOGIC")
    print("-" * 40)
    print("   Step 1: Quality Control")
    print("      → Fail if: MediaTopic failed, text invalid, too short/long")
    print("      → Continue if: All quality checks pass")
    print()
    print("   Step 2: Main Keyword Check")
    print("      → Fail if: No main sugar keywords AND exclusion keywords present")
    print("      → Continue if: Main sugar keywords found")
    print()
    print("   Step 3: Secondary Filter (Event + Agriculture)")
    print("      → Pass immediately if: Both event and agriculture keywords found")
    print("      → Continue if: Secondary filter not triggered")
    print()
    print("   Step 4: Context Zone Check")
    print("      → Fail if: No context zones matched")
    print("      → Pass if: At least one context zone matched")
    print()
    print("   Step 5: Structured Data Extraction")
    print("      → Extract any structured pricing data present")
    print("      → Pass regardless of structured data findings")
    print()
    
    # 8. Examples
    print("8. EXAMPLE FILTER APPLICATIONS")
    print("-" * 40)
    print("   Example 1: PASS - 'Brazilian sugar exports are rising due to market price changes.'")
    print("      → Main keywords: 'sugar' ✓")
    print("      → Context zones: 'market', 'region' ✓")
    print()
    print("   Example 2: FAIL - 'Copper prices are rising in the commodity market.'")
    print("      → Main keywords: None ✗")
    print("      → Exclusion keywords: 'copper' → REJECT")
    print()
    print("   Example 3: PASS (fast-track) - 'Sugar production in Brazil affected by drought conditions.'")
    print("      → Main keywords: 'sugar' ✓")
    print("      → Secondary filter: 'drought' (event) + 'production' (agriculture) ✓")
    print()
    print("   Example 4: FAIL - 'Generic market news about inflation and interest rates.'")
    print("      → Main keywords: None ✗")
    print("      → Exclusion keywords: 'generic market news' → REJECT")
    print()
    
    print("=" * 80)
    print("END OF SUMMARY")
    print("=" * 80)

def generate_keyword_list_file():
    """Generate a simple text file with all keywords organized by category"""
    
    filter_data = extract_filter_data()
    if not filter_data:
        return
    
    with open("sugar_keywords_list.txt", "w") as f:
        f.write("SUGAR NEWS PIPELINE - KEYWORDS LIST\n")
        f.write("=" * 50 + "\n\n")
        
        # Main Keywords
        f.write("MAIN KEYWORDS (Primary Sugar Terms):\n")
        f.write("-" * 35 + "\n")
        if 'main' in filter_data['keywords_dict']:
            for keyword in filter_data['keywords_dict']['main']:
                f.write(f"• {keyword}\n")
        f.write("\n")
        
        # Exclusion Keywords
        f.write("EXCLUSION KEYWORDS (Non-Sugar Commodities):\n")
        f.write("-" * 45 + "\n")
        for keyword in filter_data['exclusion_keywords']:
            f.write(f"• {keyword}\n")
        f.write("\n")
        
        # Context Zone Keywords
        f.write("CONTEXT ZONE KEYWORDS:\n")
        f.write("-" * 25 + "\n")
        
        # Market Zone
        f.write("\nMarket Zone:\n")
        if 'market' in filter_data['keywords_dict']:
            for keyword in filter_data['keywords_dict']['market']:
                f.write(f"  • {keyword}\n")
        
        # Supply Chain Zone
        f.write("\nSupply Chain Zone:\n")
        if 'supply_chain' in filter_data['keywords_dict']:
            for keyword in filter_data['keywords_dict']['supply_chain']:
                f.write(f"  • {keyword}\n")
        
        # Event Zone
        f.write("\nEvent Zone:\n")
        if 'event' in filter_data['keywords_dict']:
            for keyword in filter_data['keywords_dict']['event']:
                f.write(f"  • {keyword}\n")
        
        # Region Zone
        f.write("\nRegion Zone:\n")
        if 'region' in filter_data['keywords_dict']:
            for keyword in filter_data['keywords_dict']['region']:
                f.write(f"  • {keyword}\n")
    
    print("Generated: sugar_keywords_list.txt")

if __name__ == "__main__":
    print_filter_summary()
    generate_keyword_list_file()
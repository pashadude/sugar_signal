import sys
import json
from sugar_triage_filter import triage_filter

test_cases = [
    # Clearly relevant, English
    ("Brazilian sugar exports are rising due to market price changes.", True),
    # Multilingual: Chinese (with English sugar keyword)
    ("中国的sugar出口量因市场价格变化而增加。", True),
    # Multilingual: Spanish (with English sugar keyword)
    ("El mercado de azúcar en Brasil está cambiando rápidamente.", True),
    # Multilingual: Arabic (with English sugar keyword)
    ("ارتفعت صادرات السكر البرازيلية بسبب تغيرات الأسعار في السوق.", True),
    # Edge: Empty string
    ("", False),
    # Edge: Only whitespace
    ("     ", False),
    # Edge: Too short
    ("sugar", False),
    # Edge: Only punctuation
    ("!!! ??? ...", False),
    # Edge: Very long text
    ("sugar " * 2000, False),  # Exceeds max_length
    # Noisy: Typos in main keyword
    ("Brazilian sugr exports are rising due to market price changes.", False),
    # Noisy: Random characters
    ("asdkjhasd 12312 !@# sugar Brazil", True),
    # Noisy: Mixed languages
    ("Sucre production in Brasil está aumentando.", False),
    # Irrelevant: No main keyword
    ("The weather in Brazil is sunny and warm.", False),
    # Irrelevant: Market context but no main keyword
    ("Brazilian exports are rising due to market price changes.", False),
    # Relevant: All context zones present
    ("Sugar production in Brazil is affected by drought, impacting exports and market prices.", True),
    # Relevant: Only main and one context zone
    ("Sugar prices are rising in the market.", True),
    # Relevant: Main keyword in a phrase
    ("The NY11 sugar contract closed higher today.", True),
    # Irrelevant: Only context keywords, no main
    ("Brazilian exports and market prices are rising.", False),
    # Edge: Media topic pre-filtering failed
    ("Sugar production in Brazil is affected by drought.", False, False),

    # --- New: Exclusion of non-sugar commodities ---
    ("Copper prices rose sharply today.", False),
    ("Cocoa futures fell as oil prices fluctuated.", False),
    ("Cotton and gas markets are volatile.", False),
    ("Sugar and copper prices both rose, but focus is on copper.", True),  # Should pass, sugar present
    ("NY11 sugar contract and Brent oil both closed higher.", True),  # Should pass, sugar present

    # --- New: Structured pricing data extraction ---
    ("""
    | Contract | Date       | Price  | Volume |
    |----------|------------|--------|--------|
    | NY11     | 2025-10-19 | 27.50  | 12000  |
    | Copper   | 2025-10-19 | 8.50   | 5000   |
    """, True),

    ("- NY11 sugar: 27.50 (2025-10-19)\n- Copper: 8.50 (2025-10-19)", True),

    ("1. NY11 sugar contract: 27.50 USD, volume 12000\n2. Brent oil: 90.00 USD", True),
]

results = []
for idx, case in enumerate(test_cases):
    if len(case) == 3:
        text, expected, media_topic = case
        result = triage_filter(text, media_topic_passed=media_topic)
    else:
        text, expected = case
        result = triage_filter(text)
    results.append({
        "case": idx + 1,
        "input": text,
        "expected_passed": expected,
        "actual_passed": result["passed"],
        "reason": result["reason"],
        "matched_zones": result["matched_zones"],
        "matched_keywords": result["matched_keywords"],
        "extracted_sugar_pricing": result.get("extracted_sugar_pricing", [])
    })

print(json.dumps(results, ensure_ascii=False, indent=2))
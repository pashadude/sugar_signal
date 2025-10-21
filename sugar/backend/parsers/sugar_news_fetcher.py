import sys
print("Python executable:", sys.executable)
print("sys.path:", sys.path)
#!/usr/bin/env python
"""
Sugar News Fetcher with Unified Filtering Logic

- Integrates normalization pipeline (translation, typo correction, slang mapping, punctuation normalization, edge case handling)
- Applies keyword-based filtering (main, exclusion, context zone keywords) with multilingual support
- Implements triage logic: quality controls, context checks, structured pricing extraction
- Robust to noise, supports multilingual news, outputs structured results
"""

import os
import sys
import argparse
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Load environment variables
load_dotenv()

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.api.opoint.opoint_api import OpointAPI
from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline
from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
from sugar.backend.parsers.news_parser import (
    build_search_query,
    save_to_database,
    clean_html,
    generate_article_id
)
from sugar.backend.parsers.source_filter import filter_trusted_sources

# Sugar asset configuration
SUGAR_CONFIG = {
    'keywords_main': [
        "sugar", "sugarcane", "sugar beet", "whites", "NY11", "LSU", "LON No. 5",
        # Multilingual
        "sucre", "azúcar", "zucchero", "сахар", "سكر", "शक्कर", "gula", "şeker", "cukier"
    ],
    'keywords_exclusion': [
        # Non-sugar commodities and generic market news (from sugar_triage_filter.py)
        "copper", "cocoa", "cotton", "oil", "gas", "crude", "energy", "aluminum", "nickel",
        "zinc", "lead", "tin", "wheat", "corn", "soy", "soybean", "coffee", "tea", "rubber",
        "palm", "gold", "silver", "platinum", "palladium", "iron", "steel", "coal", "uranium",
        "natural gas", "petroleum", "oat", "barley", "livestock", "dairy", "meat", "poultry",
        "generic market news", "macro", "macro-economic", "inflation", "interest rate", "currency"
    ],
    'keywords_context_zones': [
        # Flattened context zone keywords from sugar_triage_filter.py
        "futures", "contract", "price", "market", "export", "exports", "exporter",
        "import", "imports", "importer", "shipment", "port", "tariff", "subsidy",
        "funds", "speculators", "harvest", "crushing", "yield", "production", "output", "mill",
        "ethanol", "mix", "weather", "drought", "frost", "rain", "monsoon",
        "climate", "El Niño", "La Niña", "Brazil", "Brasil", "Brazilian", "Center-South", "Centro-Sul", "India",
        "Indian", "Thailand", "Thai", "EU", "European Union", "UNICA",
        "International Sugar Organization", "ISO", "USDA"
    ]
}

MEDIA_TOPIC_IDS = ['20000373', '20000386', '20000151']

def normalize_and_filter_article(article, normalization_pipeline):
    """
    Normalize and filter a single article using the unified pipeline and triage logic.
    Returns structured result dict or None if not passed.
    """
    # Combine title and text for normalization
    raw_text = f"{article.get('title', '')}\n{article.get('text', '')}"
    normalized_text = normalization_pipeline.normalize(raw_text)

    # Clean HTML after normalization
    clean_text = clean_html(normalized_text)
    clean_title = clean_html(article.get('title', ''))

    # Apply triage filter (quality, keyword, context, pricing extraction)
    triage_result = triage_filter(clean_text)

    if not triage_result.get("passed", False):
        return None

    # Structured pricing extraction (if any)
    pricing_structured = []
    if triage_result.get("extracted_sugar_pricing"):
        pricing_structured = normalization_pipeline.normalize(
            sugar_pricing_lines=triage_result["extracted_sugar_pricing"]
        )

    # Compose structured result
    result = {
        "id": generate_article_id(
            article.get('url', ''),
            clean_title,
            article.get('published_date', ''),
            "Sugar"
        ),
        "site_name": article.get('site_name', ''),
        "clean_title": clean_title,
        "clean_text": clean_text,
        "published_date": article.get('published_date', ''),
        "url": article.get('url', ''),
        "score": article.get('score', None),
        "matched_zones": triage_result.get("matched_zones", []),
        "matched_keywords": triage_result.get("matched_keywords", []),
        "structured_pricing": pricing_structured,
        "raw_article": article
    }
    return result

def fetch_sugar_articles_for_period(api_key, start_date, end_date, topic_ids, max_articles=30000, normalization_pipeline=None):
    """
    Fetch and process sugar news articles for a given period and topic IDs.
    Returns a DataFrame of structured, filtered articles.
    """
    api = OpointAPI(api_key=api_key)
    search_query = build_search_query(topic_ids, None, None)

    print(f"Fetching sugar articles from {start_date.date()} to {end_date.date()}")

    results = api.search_site_and_articles(
        site_name=None,
        search_text=search_query,
        num_articles=max_articles,
        min_score=0.77,
        start_date=start_date,
        end_date=end_date
    )

    if results.empty:
        print(f"No articles found for sugar in {start_date.date()}")
        return pd.DataFrame()

    # Filter for main keywords (multilingual)
    results['contains_main_keywords'] = results.apply(
        lambda row: any(
            kw.lower() in (row.get('title', '').lower() + " " + row.get('text', '').lower())
            for kw in SUGAR_CONFIG['keywords_main']
        ),
        axis=1
    )
    filtered_results = results[results['contains_main_keywords']].copy()
    if filtered_results.empty:
        print(f"No main keyword-matching articles for sugar in {start_date.date()}")
        return pd.DataFrame()

    # Exclude articles with exclusion keywords ONLY if no sugar keywords present
    def contains_exclusion(text):
        return [kw for kw in SUGAR_CONFIG['keywords_exclusion'] if kw.lower() in text.lower()]
    def contains_inclusion(text):
        return [kw for kw in SUGAR_CONFIG['keywords_main'] if kw.lower() in text.lower()]

    # Log only inclusion/exclusion keywords, not full text
    def log_keywords(row):
        incl = contains_inclusion(row.get('title', '') + " " + row.get('text', ''))
        excl = contains_exclusion(row.get('title', '') + " " + row.get('text', ''))
        print(f"INCLUSION KEYWORDS: {incl} | EXCLUSION KEYWORDS: {excl}")

    # Only exclude if no inclusion keywords
    filtered_results = filtered_results[
        ~filtered_results.apply(
            lambda row: not contains_inclusion(row.get('title', '') + " " + row.get('text', '')) and contains_exclusion(row.get('title', '') + " " + row.get('text', '')),
            axis=1
        )
    ]
    # Log inclusion/exclusion keywords for each article
    filtered_results.apply(log_keywords, axis=1)

    if filtered_results.empty:
        print(f"All articles excluded by exclusion keywords for sugar in {start_date.date()}")
        return pd.DataFrame()

    # Apply normalization and triage pipeline
    structured_articles = []
    for _, article in filtered_results.iterrows():
        result = normalize_and_filter_article(article, normalization_pipeline)
        if result:
            structured_articles.append(result)

    if not structured_articles:
        print(f"No articles passed triage for sugar in {start_date.date()}")
        return pd.DataFrame()

    # Convert to DataFrame
    df_structured = pd.DataFrame(structured_articles)

    # Filter for trusted sources
    df_structured = filter_trusted_sources(df_structured, verbose=True)

    return df_structured

def generate_date_ranges(months_back=12):
    """Generate list of (start_date, end_date) tuples for the last N months"""
    date_ranges = []
    current_date = datetime.now()
    for i in range(months_back):
        target_date = current_date - timedelta(days=30 * i)
        start_of_month = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_of_month.month == 12:
            end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1) - timedelta(seconds=1)
        else:
            end_of_month = start_of_month.replace(month=start_of_month.month + 1) - timedelta(seconds=1)
        date_ranges.append((start_of_month, end_of_month))
    return date_ranges

def main():
    parser = argparse.ArgumentParser(description="Fetch and filter sugar news articles with unified logic")
    parser.add_argument('--dry-run', action='store_true', help='Print what would be done without executing')
    parser.add_argument('--max-workers', type=int, default=7, help='Maximum number of concurrent workers (default: 3)')
    parser.add_argument('--months-back', type=int, default=120, help='Number of months back to fetch (default: 12)')
    parser.add_argument('--max-articles', type=int, default=30000, help='Maximum articles per request (default: 30000)')
    args = parser.parse_args()

    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("Error: OPOINT_API_KEY environment variable not found")
        return

    date_ranges = generate_date_ranges(args.months_back)
    total_tasks = len(date_ranges) * len(MEDIA_TOPIC_IDS)
    print(f"Starting sugar news fetch across {len(date_ranges)} months")
    print(f"Using {len(MEDIA_TOPIC_IDS)} media topic IDs: {', '.join(MEDIA_TOPIC_IDS)}")
    print(f"Total tasks: {total_tasks}")
    print(f"Max workers: {args.max_workers}")

    if args.dry_run:
        print("\n=== DRY RUN - Would process the following ===")
        for start_date, end_date in date_ranges:
            print(f"Period: {start_date.date()} to {end_date.date()}")
        return

    normalization_pipeline = LanguageNormalizationPipeline()

    start_time = datetime.now()
    total_saved = 0
    all_structured = []

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_task = {}
        for start_date, end_date in date_ranges:
            for topic_id in MEDIA_TOPIC_IDS:
                future = executor.submit(
                    fetch_sugar_articles_for_period,
                    api_key, start_date, end_date, [topic_id], args.max_articles, normalization_pipeline
                )
                future_to_task[future] = (start_date, end_date, topic_id)

        for future in as_completed(future_to_task):
            start_date, end_date, topic_id = future_to_task[future]
            try:
                df_structured = future.result()
                if not df_structured.empty:
                    all_structured.append(df_structured)
                    total_saved += len(df_structured)
                time.sleep(0.1)
            except Exception as e:
                print(f"Task failed for {start_date.date()} topic:{topic_id}: {str(e)}")

    # Concatenate all results
    if all_structured:
        final_df = pd.concat(all_structured, ignore_index=True)
        # Save to database
        search_metadata = {
            'topic_ids': MEDIA_TOPIC_IDS,
            'keywords_main': SUGAR_CONFIG['keywords_main'],
            'keywords_exclusion': SUGAR_CONFIG['keywords_exclusion'],
            'keywords_context_zones': SUGAR_CONFIG['keywords_context_zones'],
            'search_period': f"{date_ranges[-1][0].date()} to {date_ranges[0][1].date()}"
        }
        saved_count = save_to_database(final_df, search_metadata, "Sugar")
        print(f"Saved {saved_count} sugar articles to database")
    else:
        print("No sugar articles passed unified filtering logic.")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n=== SUGAR NEWS FETCH COMPLETED ===")
    print(f"Total articles saved: {total_saved}")
    print(f"Total duration: {duration}")
    print(f"Average time per task: {duration.total_seconds() / total_tasks:.2f} seconds")
    print(f"Date range: {date_ranges[-1][0].date()} to {date_ranges[0][1].date()}")

if __name__ == "__main__":
    main()
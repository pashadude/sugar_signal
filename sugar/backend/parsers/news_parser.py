#!/usr/bin/env python
"""
Generic news parser for fetching articles based on configurable topics, person entities, 
company entities, and keywords using the OPOINT API.
"""
import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import re
import time
import argparse
import hashlib
from clickhouse_driver import Client

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.api.opoint.opoint_api import OpointAPI
from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
from sugar.backend.parsers.source_filter import is_trusted_source, filter_trusted_sources

def clean_html(text):
    """Remove HTML tags and clean up text"""
    if not text:
        return ""
    
    # Handle the special case for <escaped> text first
    # This is a literal text that should not be treated as HTML
    text = text.replace('<escaped>', '___LITERAL_ESCAPED___')
    
    # Remove script and style tags with their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Replace HTML tags with spaces to preserve word separation, but preserve HTML entities
    # First, temporarily protect HTML entities
    text = re.sub(r'(&[a-zA-Z0-9#]+;)', '___ENTITY___\\1___ENTITY___', text)
    
    # Replace HTML tags with spaces
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Restore HTML entities
    text = re.sub(r'___ENTITY___(&[a-zA-Z0-9#]+;)___ENTITY___', '\\1', text)
    
    # Restore the literal <escaped> text
    text = text.replace('___LITERAL_ESCAPED___', '<escaped>')
    
    # Normalize whitespace but preserve punctuation spacing
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,!?])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def contains_keywords(text, keywords):
    """Check if text contains any of the specified keywords (whole word matching)"""
    if not isinstance(text, str) or not keywords:
        return False
    text_lower = text.lower()
    for kw in keywords:
        # Use word boundaries to ensure whole word matching
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False

def build_search_query(topic_ids, person_entities, company_entities, sugar_sources=None):
    """Build search query string for OPOINT API"""
    query_parts = []
    
    # Add topic conditions (prefix with "1" to create TARGET_MEDIATOPIC_ID)
    if topic_ids:
        topic_conditions = [f"(topic:1{topic_id})" for topic_id in topic_ids]
        if len(topic_conditions) == 1:
            query_parts.append(topic_conditions[0])
        else:
            query_parts.append(f"{' OR '.join(topic_conditions)}")
    
    # Add person entity conditions
    #office leaders
    if person_entities:
        person_conditions = [f'(person:"{entity}")' for entity in person_entities]
        if len(person_conditions) == 1:
            query_parts.append(person_conditions[0])
        else:
            query_parts.append(f"{' OR '.join(person_conditions)}")
    
    # Add company entity conditions
    # companies in suger
    if company_entities:
        company_conditions = [f'(company:"{entity}")' for entity in company_entities]
        if len(company_conditions) == 1:
            query_parts.append(company_conditions[0])
        else:
            query_parts.append(f"{' AND '.join(company_conditions)}")
    
    # Add sugar source conditions if provided
    if sugar_sources:
        source_conditions = [f'(source:"{source}")' for source in sugar_sources]
        if len(source_conditions) == 1:
            query_parts.append(source_conditions[0])
        else:
            query_parts.append(f"({' OR '.join(source_conditions)})")
    
    # Combine all parts with AND
    if query_parts:
        return " AND ".join(query_parts)
    else:
        return ""

def generate_article_id(url, title, published_date, asset):
    """Generate a unique ID for an article based on URL, title, date, and asset"""
    content = f"{url}_{title}_{published_date}_{asset}"
    return hashlib.md5(content.encode()).hexdigest()



def save_to_database(articles_df, search_metadata, asset=None):
    """Save articles to ClickHouse database (only trusted sources)"""
    try:
        # Filter out non-trusted sources before saving
        filtered_df = filter_trusted_sources(articles_df)
        
        if filtered_df.empty:
            print("No articles from trusted sources to save")
            return 0
        
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        
        # Prepare data for insertion
        records = []
        for _, row in filtered_df.iterrows():
            # Determine asset value - use individual article asset if available, otherwise use the provided asset
            article_asset = row.get('asset', asset) if 'asset' in row else asset
            
            # Generate unique ID for the article (including asset for proper deduplication)
            article_id = generate_article_id(
                row.get('url', ''),
                row.get('title', ''),
                row.get('published_date', ''),
                article_asset
            )
            
            # Prepare metadata as JSON
            metadata = {
                'search_topic_ids': search_metadata.get('topic_ids'),
                'search_person_entities': search_metadata.get('person_entities'),
                'search_company_entities': search_metadata.get('company_entities'),
                'search_keywords': search_metadata.get('keywords'),
                'score': row.get('score'),
                'triage_passed': row.get('triage_passed', None),
                'triage_reason': row.get('triage_reason', None)
            }
            
            # Parse published_date to datetime
            try:
                if pd.notna(row.get('published_date')):
                    pub_date = pd.to_datetime(row['published_date'])
                else:
                    pub_date = datetime.now()
            except:
                pub_date = datetime.now()
            
            # Add created_at as now
            created_at = datetime.now()
            
            record = (
                article_id,
                pub_date,
                row.get('site_name', ''),
                row.get('clean_title', ''),
                row.get('clean_text', ''),
                json.dumps(metadata),
                created_at,
                article_asset
            )
            records.append(record)
        
        # Insert into database
        print(f"Executing INSERT with {len(records)} records...")
        # Write to news.news table
        result = client.execute(
            'INSERT INTO news.news (id, datetime, source, title, text, metadata, created_at, asset) VALUES',
            records
        )
        print(f"INSERT statement executed successfully, result: {result}")
        
        print(f"Successfully saved {len(records)} articles from trusted sources to ClickHouse database")
        return len(records)
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and analyze news articles based on topics and entities")
    
    # Topic arguments
    parser.add_argument('--topic-ids', nargs='+', help='List of media topic IDs to search for')
    
    # Entity arguments
    parser.add_argument('--person-entities', nargs='+', help='List of person entities to search for (e.g., "John Doe")')
    parser.add_argument('--company-entities', nargs='+', help='List of company entities to search for (e.g., "Apple Inc")')
    
    # Content filtering
    parser.add_argument('--keywords', nargs='+', help='Keywords to filter content (case-insensitive)')
    
    # Asset (required)
    parser.add_argument('--asset', type=str, required=True, help='Asset name (obligatory field)')
    
    # Date parameters - flexible options
    parser.add_argument('--days-back', type=int, help='Number of days back to fetch articles (alternative to start/end dates)')
    parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format (e.g., 2024-01-01)')
    parser.add_argument('--end-date', type=str, help='End date in YYYY-MM-DD format (e.g., 2024-01-31)')
    
    # API parameters
    parser.add_argument('--num-articles', type=int, default=50, help='Number of articles to fetch (default: 50)')
    parser.add_argument('--min-score', type=float, default=0.75, help='Minimum relevance score (default: 0.75)')
    
    # Database options
    parser.add_argument('--dry-run', action='store_true', help='Print results without saving to database')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Validate inputs
    if not any([args.topic_ids, args.person_entities, args.company_entities]):
        print("Error: At least one of --topic-ids, --person-entities, or --company-entities must be specified")
        sys.exit(1)
    
    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("Error: OPOINT_API_KEY environment variable not found")
        sys.exit(1)

    # Handle date parameters
    start_date = None
    end_date = None
    
    if args.start_date and args.end_date:
        # Use explicit start and end dates
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            if start_date > end_date:
                print("Error: Start date must be before or equal to end date")
                sys.exit(1)
        except ValueError as e:
            print(f"Error parsing dates: {e}")
            print("Please use YYYY-MM-DD format (e.g., 2024-01-01)")
            sys.exit(1)
    elif args.days_back:
        # Use days_back parameter
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days_back)
    elif args.start_date or args.end_date:
        print("Error: If using explicit dates, both --start-date and --end-date must be specified")
        sys.exit(1)
    else:
        # Default to last 7 days if no date parameters provided
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

    # Build search query
    search_query = build_search_query(args.topic_ids, args.person_entities, args.company_entities)
    if not search_query:
        print("Error: Could not build search query from provided inputs")
        sys.exit(1)
    
    print(f"Search query: {search_query}")

    # Fetch articles for specified time period
    api = OpointAPI(api_key=api_key)

    print(f"Fetching articles from {start_date} to {end_date}")
    print(f"Topic IDs: {args.topic_ids}")
    print(f"Person entities: {args.person_entities}")
    print(f"Company entities: {args.company_entities}")
    
    results = api.search_site_and_articles(
        site_name=None,
        search_text=search_query,
        language='en',
        num_articles=args.num_articles,
        min_score=args.min_score,
        start_date=start_date,
        end_date=end_date
    )

    if results.empty:
        print("No articles found for the selected criteria.")
        return

    print(f"Found {len(results)} articles before filtering")

    # Filter for keyword content if specified
    if args.keywords:
        print(f"Filtering articles for keywords: {args.keywords}")
        results['contains_keywords'] = results.apply(
            lambda row: contains_keywords(row.get('title', ''), args.keywords) or 
                       contains_keywords(row.get('text', ''), args.keywords),
            axis=1
        )
        filtered_results = results[results['contains_keywords']].copy()
        if filtered_results.empty:
            print("No articles found matching the specified keywords.")
            return
        print(f"Found {len(filtered_results)} articles after keyword filtering")
    else:
        filtered_results = results.copy()

    # Clean text content
    filtered_results['clean_text'] = filtered_results['text'].apply(clean_html)
    filtered_results['clean_title'] = filtered_results['title'].apply(clean_html)
    
    # Prepare search metadata
    search_metadata = {
        'topic_ids': args.topic_ids,
        'person_entities': args.person_entities,
        'company_entities': args.company_entities,
        'keywords': args.keywords
    }

    # Add score field based on position (lower position = higher relevance)
    if 'position' in filtered_results.columns:
        # Convert position to relevance score (position 1 = highest score)
        max_position = filtered_results['position'].max() if not filtered_results['position'].isna().all() else 1
        filtered_results['score'] = 1.0 - (filtered_results['position'] - 1) / max_position
    else:
        filtered_results['score'] = None

    # Save results
    if args.dry_run:
        # Apply source filtering for dry run preview as well
        trusted_filtered_results = filter_trusted_sources(filtered_results)
        
        print("\n=== DRY RUN - Results Preview ===")
        print(f"Would save {len(trusted_filtered_results)} articles from trusted sources to database")
        print("\nSample articles:")
        for i, (_, row) in enumerate(trusted_filtered_results.head(3).iterrows()):
            print(f"\n{i+1}. {row.get('clean_title', 'No title')}")
            print(f"   Site: {row.get('site_name', 'Unknown')}")
            print(f"   Source: {row.get('source_name', 'Unknown')}")
            print(f"   Date: {row.get('published_date', 'Unknown')}")
            print(f"   URL: {row.get('url', 'No URL')}")
            print(f"   Score: {row.get('score', 'N/A')}")
            print(f"   Language: {row.get('language', 'Unknown')}")
            print(f"   Author: {row.get('author', 'Unknown')}")
            if row.get('sentiment'):
                print(f"   Sentiment: {row.get('sentiment')} ({row.get('sentiment_score', 'N/A')})")
            
            # Show preview of text content
            text_preview = row.get('clean_text', '')[:200] + '...' if len(row.get('clean_text', '')) > 200 else row.get('clean_text', '')
            print(f"   Text preview: {text_preview}")
    else:
        try:
            saved_count = save_to_database(filtered_results, search_metadata, args.asset)
            print(f"Successfully saved {saved_count} articles to database")
        except Exception as e:
            print(f"Failed to save to database: {e}")
            return
    
    # Print summary statistics
    print("\n=== Summary ===")
    print(f"Total articles found: {len(filtered_results)}")
    if 'site_name' in filtered_results.columns:
        top_sources = filtered_results['site_name'].value_counts().head().to_dict()
        print(f"Top sources: {top_sources}")
    if 'published_date' in filtered_results.columns:
        # Handle both datetime and string formats
        try:
            date_min = filtered_results['published_date'].min()
            date_max = filtered_results['published_date'].max()
            print(f"Date range: {date_min} to {date_max}")
        except:
            print("Date range: Unable to determine")

if __name__ == "__main__":
    main() 
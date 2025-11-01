#!/usr/bin/env python
"""
Source filtering utilities for news parsers.
Provides functionality to filter out non-trusted news sources.
"""

def get_sugar_trusted_sources():
    """
    Return a set of sugar-specific trusted news sources.
    
    These sources have been identified as high-quality, reliable sources
    for sugar industry news and should be prioritized in sugar news fetching.
    This list is synchronized with the SUGAR_SOURCES configuration in sugar_news_fetcher.py.
    Any changes to this list should be reflected in that configuration as well.
    
    IMPORTANT: When updating this list, ensure that:
    1. All source names are also added to the SUGAR_SOURCES configuration in sugar_news_fetcher.py
    2. The source names match exactly with those in the SUGAR_SOURCES configuration
    3. Both files remain synchronized to maintain consistency in the sugar news fetching pipeline
    
    Returns:
        set: Set of sugar-specific trusted source names
    """
    return {
        # Sugar Industry Publications
        'Food Processing',
        'Sugar Producer',
        
        # Agricultural Commodity News Sources
        'Argus Media',
        'Fastmarkets',
        'Ag Update',
        'Agriinsite',
        'Agronews',
        'ICE',
        'Tridge',
        
        # Trade Publications Focused on Sugar and Sweeteners
        'Food Navigator USA',
        'Food Navigator',
        'Benzinga',
        'Yahoo! Finance',
        'Business Insider',
        'Investing',
        'CNBC',
        'Investing.com Brasil',
        'Nasdaq',
        'Barchart',
        'Market Screener',
        'Barron\'s',
        'Trading Economics',
        'Chini Mandi',
        'Globy',
        'CME Group',
        
        # Government and International Organizations
        'USDA',
        'FAO'
    }

def get_sugar_trusted_source_ids():
    """
    Return a set of sugar-specific trusted source IDs.
    
    These source IDs correspond to the trusted source names and are used
    for more reliable source filtering when IDs are available in the API response.
    This list is synchronized with the SUGAR_SOURCES configuration in sugar_news_fetcher.py.
    
    Returns:
        set: Set of sugar-specific trusted source IDs
    """
    return {
        # Sugar Industry Publications
        171463,  # Food Processing
        124631,  # Sugar Producer
        
        # Agricultural Commodity News Sources
        82120,   # Argus Media
        30542,   # Fastmarkets
        335679,  # Ag Update
        449222,  # Agriinsite
        256958,  # Agronews
        999,     # ICE
        448815,  # Tridge
        
        # Trade Publications Focused on Sugar and Sweeteners
        26214,   # Food Navigator USA
        241270,  # Food Navigator
        23564,   # Benzinga
        3478,    # Yahoo! Finance
        12323,   # Business Insider
        10836,   # Investing
        22991,   # CNBC
        173901,  # Investing.com Brasil
        913,     # Nasdaq
        124923,  # Barchart
        37015,   # Market Screener
        28875,   # Barron's
        213991,  # Trading Economics
        442001,  # Chini Mandi
        464928,  # Globy
        273765, # CME Group
        
        # Government and International Organizations
        15086,   # USDA
        53626    # FAO
    }

def get_non_trusted_sources():
    """
    Return a set of non-trusted news sources to filter out.
    
    These sources have been identified as unreliable, spam, or low-quality
    and should be excluded from news analysis.
    
    Returns:
        set: Set of non-trusted source names
    """
    return {
        # Local/Regional News Sources (Often Low Quality)
        'Guelph Today',
        'Timminstoday',
        'Herriman Journal',
        'St. Marys Daily Press',
        'Draper Journal',
        'Hattiesburg',
        'Gulf And Main Magazine',
        'Holliston',
        'Greenville Business Magazine',
        'The Evening Leader',
        'Connect Fayetteville',
        'The Brewton Standard',
        'Elizabethton Star',
        'Austin Herald',
        'Demopolis Times',
        'Click On Detroit',
        'Hanauer Anzeiger',
        'San Rafael',
        'Midvale Journal',
        'Magdeburger News',
        'Luvernejournal',
        'Nipawin Journal',
        'Windsor Weekly',
        'The Oxford Eagle',
        'La Grange News',
        'The Lowndes Signal',
        'Walnutcreekmagazine.com',
        'The Atmore Advance',
        'The Tidewater News',
        'South Salt Lake Journal',
        'Tallassee Tribune',
        'The Greenville Advocate',
        'Blue Grass Live',
        'Vicks Burg Post',
        'Albert Lea Tribune',
        'Sandy Journal',
        'Suffolk News Herald',
        'The Free Library',
        'Valley Journals',
        'Millcreek Journal',
        'Columbia Business Monthly',
        'Valley Times News',
        'Wnc Business',
        
        # Aggregators and Low-Quality Sources
        'Toti',
        'Deal Town',
        'Head Topics',
        'Listcorp',
        'Recently Heard',
        
        # Crypto/Financial Spam Sources
        'BITRSS Crypto and Bitcoin World News',
        'Bit News Bot',
        'Worldstockmarket.net',
        
        # Generic Content/SEO Sources
        'Artikelverzeichnis Online',
        'Initiative Mittelstand',
        'SlideShare'
    }

def is_trusted_source(source_name, source_id=None):
    """
    Check if a source is trusted (not in the non-trusted list or in sugar-specific trusted sources).
    
    Args:
        source_name (str): Name of the news source
        source_id (int, optional): ID of the news source for more reliable checking
        
    Returns:
        bool: True if source is trusted, False otherwise
    """
    # First check by ID if available (more reliable)
    if source_id is not None:
        sugar_trusted_ids = get_sugar_trusted_source_ids()
        if source_id in sugar_trusted_ids:
            return True
    
    # Fall back to name-based checking
    if not source_name:
        return False
    
    non_trusted = get_non_trusted_sources()
    sugar_trusted = get_sugar_trusted_sources()
    
    # Case-sensitive exact match
    normalized_source = source_name.strip()
    
    # Source is trusted if it's in sugar-specific trusted sources OR not in non-trusted sources
    return normalized_source in sugar_trusted or normalized_source not in non_trusted

def filter_trusted_sources(articles_df, verbose=True):
    """
    Filter out articles from non-trusted sources.
    
    Args:
        articles_df (pd.DataFrame): DataFrame containing articles with 'site_name' column
        verbose (bool): Whether to print filtering statistics
        
    Returns:
        pd.DataFrame: Filtered DataFrame containing only articles from trusted sources
    """
    if articles_df.empty:
        return articles_df
    
    # Get initial count
    initial_count = len(articles_df)
    
    # Filter for trusted sources using both name and ID if available
    if 'site_id' in articles_df.columns:
        # Use both name and ID for more reliable filtering
        trusted_mask = articles_df.apply(
            lambda row: is_trusted_source(row.get('site_name'), row.get('site_id')),
            axis=1
        )
    else:
        # Fall back to name-based filtering only
        trusted_mask = articles_df['site_name'].apply(lambda x: is_trusted_source(x))
    
    filtered_df = articles_df[trusted_mask].copy()
    
    # Report filtering results
    filtered_count = initial_count - len(filtered_df)
    if verbose and filtered_count > 0:
        print(f"Filtered out {filtered_count} articles from non-trusted sources")
        
        # Show which sources were filtered
        non_trusted_sources = articles_df[~trusted_mask]['site_name'].value_counts()
        if len(non_trusted_sources) > 0:
            print("Non-trusted sources filtered:")
            for source, count in non_trusted_sources.items():
                print(f"  - {source}: {count} articles")
    
    return filtered_df

def get_source_statistics(articles_df):
    """
    Get statistics about trusted vs non-trusted sources in a DataFrame.
    
    Args:
        articles_df (pd.DataFrame): DataFrame containing articles with 'site_name' column
        
    Returns:
        dict: Statistics about source distribution
    """
    if articles_df.empty:
        return {
            'total_articles': 0,
            'trusted_articles': 0,
            'non_trusted_articles': 0,
            'trusted_sources': [],
            'non_trusted_sources': []
        }
    
    # Classify sources using both name and ID if available
    if 'site_id' in articles_df.columns:
        # Use both name and ID for more reliable filtering
        trusted_mask = articles_df.apply(
            lambda row: is_trusted_source(row.get('site_name'), row.get('site_id')),
            axis=1
        )
    else:
        # Fall back to name-based filtering only
        trusted_mask = articles_df['site_name'].apply(lambda x: is_trusted_source(x))
    
    trusted_sources = articles_df[trusted_mask]['site_name'].value_counts().to_dict()
    non_trusted_sources = articles_df[~trusted_mask]['site_name'].value_counts().to_dict()
    
    return {
        'total_articles': len(articles_df),
        'trusted_articles': trusted_mask.sum(),
        'non_trusted_articles': (~trusted_mask).sum(),
        'trusted_sources': trusted_sources,
        'non_trusted_sources': non_trusted_sources
    }

def add_non_trusted_source(source_name):
    """
    Add a new source to the non-trusted list.
    
    Note: This function is for reference only. To permanently add sources,
    update the get_non_trusted_sources() function directly.
    
    Args:
        source_name (str): Name of the source to add to non-trusted list
    """
    print(f"To permanently add '{source_name}' to non-trusted sources,")
    print("update the get_non_trusted_sources() function in this module.")

def validate_source_name(source_name):
    """
    Validate and normalize a source name.
    
    Args:
        source_name (str): Source name to validate
        
    Returns:
        str: Normalized source name, or None if invalid
    """
    if not source_name or not isinstance(source_name, str):
        return None
    
    # Basic normalization
    normalized = source_name.strip()
    
    # Remove common prefixes/suffixes that might cause matching issues
    # This is conservative - only remove obvious noise
    if len(normalized) < 3:  # Too short to be a real source name
        return None
    
    return normalized 
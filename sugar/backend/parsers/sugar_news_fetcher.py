import sys
print("Python executable:", sys.executable)
print("sys.path:", sys.path)
#!/usr/bin/env python
"""
Sugar News Fetcher with Unified Filtering Logic

- Integrates normalization pipeline (translation, typo correction, slang mapping, punctuation normalization, edge case handling)
- Applies keyword-based filtering (main, exclusion, context zone keywords) with multilingual support
- Implements triage logic: quality controls, context checks, structured pricing extraction
- Queries sugar sources separately from other sources to ensure they're not forgotten
- Applies all filtering (including source filtering) to both sugar and non-sugar sources
- Combines results after filtering for comprehensive coverage
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
import hashlib
import logging
import threading
import pickle
import tempfile
# Try to import psutil for memory monitoring, but make it optional
try:
    import psutil  # For memory monitoring
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil module not found. Memory monitoring will be disabled.")

import gc  # For garbage collection

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

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[
        logging.FileHandler('sugar_news_fetcher_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Thread-safe counter for tracking active requests
active_requests = threading.Semaphore(value=50)  # Limit concurrent API requests
request_counter = 0
request_lock = threading.Lock()

# Memory monitoring functions
def get_memory_usage():
    """Get current memory usage in MB"""
    if PSUTIL_AVAILABLE:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    else:
        # Fallback: return 0 when psutil is not available
        logger.debug("psutil not available, cannot get memory usage")
        return 0

def check_memory_usage(max_memory_mb=4000):
    """Check if memory usage is within limits, return True if OK"""
    if PSUTIL_AVAILABLE:
        current_memory = get_memory_usage()
        logger.debug(f"Current memory usage: {current_memory:.2f} MB")
        if current_memory > max_memory_mb:
            logger.warning(f"Memory usage too high: {current_memory:.2f} MB > {max_memory_mb} MB")
            return False
        return True
    else:
        # Fallback: always return True when psutil is not available
        logger.debug("psutil not available, skipping memory usage check")
        return True

def cleanup_memory():
    """Force garbage collection and clean up memory"""
    logger.debug("Running garbage collection to free memory")
    gc.collect()

def save_checkpoint(checkpoint_data, checkpoint_file):
    """Save checkpoint data to file for recovery in case of failure"""
    try:
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        logger.info(f"Checkpoint saved to {checkpoint_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {str(e)}")
        return False

def load_checkpoint(checkpoint_file):
    """Load checkpoint data from file for recovery"""
    try:
        if not os.path.exists(checkpoint_file):
            logger.info(f"No checkpoint file found at {checkpoint_file}")
            return None
        
        with open(checkpoint_file, 'rb') as f:
            checkpoint_data = pickle.load(f)
        logger.info(f"Checkpoint loaded from {checkpoint_file}")
        return checkpoint_data
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {str(e)}")
        return None

def save_intermediate_results(all_structured, batch_index, checkpoint_dir):
    """Save intermediate results to prevent data loss"""
    try:
        if not all_structured:
            return False
            
        # Create checkpoint directory if it doesn't exist
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Save intermediate results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        intermediate_file = os.path.join(checkpoint_dir, f"intermediate_results_batch_{batch_index}_{timestamp}.pkl")
        
        with open(intermediate_file, 'wb') as f:
            pickle.dump(all_structured, f)
        
        logger.info(f"Intermediate results saved to {intermediate_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save intermediate results: {str(e)}")
        return False

def load_intermediate_results(checkpoint_dir):
    """Load all intermediate results from checkpoint directory"""
    try:
        if not os.path.exists(checkpoint_dir):
            logger.info(f"No checkpoint directory found at {checkpoint_dir}")
            return []
        
        # Load all intermediate result files
        all_results = []
        checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.startswith("intermediate_results_batch_")]
        
        for file in sorted(checkpoint_files):
            file_path = os.path.join(checkpoint_dir, file)
            try:
                with open(file_path, 'rb') as f:
                    batch_results = pickle.load(f)
                    all_results.extend(batch_results)
                logger.info(f"Loaded intermediate results from {file}")
            except Exception as e:
                logger.error(f"Failed to load intermediate results from {file}: {str(e)}")
        
        return all_results
    except Exception as e:
        logger.error(f"Failed to load intermediate results: {str(e)}")
        return []

def cleanup_checkpoint_files(checkpoint_dir):
    """Clean up checkpoint files after successful completion"""
    try:
        if not os.path.exists(checkpoint_dir):
            return True
        
        checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.startswith("intermediate_results_batch_")]
        
        for file in checkpoint_files:
            file_path = os.path.join(checkpoint_dir, file)
            try:
                os.remove(file_path)
                logger.debug(f"Removed checkpoint file: {file}")
            except Exception as e:
                logger.error(f"Failed to remove checkpoint file {file}: {str(e)}")
        
        # Try to remove the directory if it's empty
        try:
            if not os.listdir(checkpoint_dir):
                os.rmdir(checkpoint_dir)
                logger.info(f"Removed empty checkpoint directory: {checkpoint_dir}")
        except Exception as e:
            logger.debug(f"Could not remove checkpoint directory {checkpoint_dir}: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to cleanup checkpoint files: {str(e)}")
        return False

# Sugar asset configuration
SUGAR_CONFIG = {
    'keywords_main': [
        "sugar", "sugarcane", "sugar beet", "whites", "NY11", "LSU", "LON No. 5",
        # Multilingual - European languages
        "sucre", "azúcar", "zucchero", "açúcar", "Zucker", "sukker", "soker", "cukor",
        "cukier", "cukr", "sahara", "ζάχαρη", "cukor", "soker", "sugar", "sukker",
        # Multilingual - Asian languages
        "शक्कर", "चीनी", "চিনি", "சர்க்கரை", "చక్కరో", "ಸಕ್ಕರೆ", "പഞ്ചശര", "සීනි",
        "شکر", "سكر", "शक्कर", "चीनी", "gula", "gularen", "gula aren", "gula merah",
        "น้ำตาล", "น้ำตาลทราย", "อ้อย", "ตะกั่ว", "茶糖", "砂糖", "糖", "설탕", "설탕물",
        # Multilingual - Other major languages
        "şeker", "şekerli", "cukier", "cukrowy", "сахар", "сахарный", "цукор", "цукровий",
        "mishukozi", "asali", "sukari", "chini", "tumbura", "sukali", "sukari", "shakar",
        "shakkar", "misri", "khanda", "gud", "jaggery", "panela", "piloncillo", "rapadura"
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
        "International Sugar Organization", "ISO", "USDA",
        
        # Multilingual context keywords - Production & Processing
        "producción", "produção", "produzione", "production", "Produktion", "produktie",
        "cosecha", "colheita", "raccolta", "harvest", "Ernte", "oogst", "zbiór",
        "moagem", "molino", "mulino", "mill", "Mühle", "molen", "młyn",
        "usina", "fábrica", "fabbrica", "factory", "Fabrik", "fabriek", "fabryka",
        
        # Multilingual context keywords - Market & Trade
        "mercado", "mercato", "market", "Markt", "markt", "rynek",
        "exportación", "exportação", "esportazione", "export", "Export", "export", "eksport",
        "importación", "importação", "importazione", "import", "Import", "import", "import",
        "preço", "prezzo", "price", "Preis", "prijs", "cena",
        "futuros", "futures", "Termin", "termijn", "terminowe",
        
        # Multilingual context keywords - Weather & Climate
        "clima", "clima", "climate", "Klima", "klimaat", "klimat",
        "sequía", "seca", "siccità", "drought", "Dürre", "droogte", "susza",
        "geada", "gelata", "gelo", "frost", "Frost", "vorst", "przymrozek",
        "chuva", "pioggia", "rain", "Regen", "regen", "deszcz",
        "monzón", "monção", "monsoon", "Monsun", "moesson", "monsun",
        
        # Multilingual context keywords - Regions
        "Brasil", "Brazil", "Brésil", "Brasilien", "Brazilië", "Brazylia",
        "Índia", "India", "Indien", "Indië", "Indie",
        "Tailandia", "Thailand", "Thaïlande", "Thailand", "Tajlandia",
        "Unión Europea", "União Europeia", "European Union", "Europäische Union", "Europese Unie", "Unia Europejska"
    ],
    'company_entities': [
        # Major agricultural trading companies and sugar producers
        "Archer Daniels Midland", "ADM", "Bunge", "Cargill", "Cargill, Inc.",
        "Louis Dreyfus Company", "LDC", "COFCO International", "Wilmar International Ltd.",
        "Copersucar", "Imperial Sugar", "Biosev", "Südzucker AG", "CropEnergies AG",
        "Tereos", "Nordzucker AG", "Tereos TTD a.s.", "Cosan S.A.", "Raízen", "Shell",
        "U.S. Sugar Corporation", "American Sugar Refining", "ASR Group", "Florida Crystals Corporation",
        "Mitr Phol Group", "Thai Roong Ruang Group", "Associated British Foods", "ABF",
        "AB Sugar", "British Sugar", "British Sugar plc", "Illovo Sugar", "ED&F Man Sugar",
        "StoneX", "Czarnikow", "CZ", "BCM Global Traders", "Viterra"
    ],
    'government_entities': [
        # Government and regulatory bodies
        "Ministry of Agriculture and Livestock", "MAPA", "UNICA", "Brazilian Sugarcane Industry Association",
        "Apex-Brasil", "Brazilian Trade and Investment Promotion Agency", "Ministry of Consumer Affairs",
        "Food and Public Distribution", "Directorate of Sugar", "Ministry of Agriculture and Farmers Welfare",
        "Directorate of Sugarcane Development", "Ministry of Industry", "Thailand",
        "Office of the Cane and Sugar Board", "OCSB"
    ],
    'person_entities': [
        # Key executives and persons in the sugar industry
        "Brian Sikes", "Roger Watchorn", "Juan R. Luciano", "Christopher M. Cuddy", "Gregory Heckman",
        "Mark Zenuk", "Margarita Louis-Dreyfus", "Michael Gelchie", "Xu Guanghong", "Wei Dong",
        "Kuok Khoon Hong", "Jean-Luc Bohbot", "Niels Pörksen", "Olivier Leducq", "Gérard Clay",
        "Rubens Ometto Silveira Mello", "Ricardo Mussa", "Isara Vongkusolkit", "Suree Asdathorn",
        "Ugrit Asadatorn", "Nicha Asadatorn", "George Weston", "Paul Kenward", "Lars Gorissen",
        "Alexandre Bauche", "Sean O'Connor", "Robin Cave", "Carlos Favaro", "Evandro Gussi",
        "Jorge Viana", "Pralhad Joshi", "Sangeet", "Shivraj Singh Chouhan", "Virendra Singh",
        "Thanakorn Wangboonkongchana", "Bainoi Suwanchatree"
    ]
}

# Sugar-specific news sources configuration
# NOTE: This list is synchronized with source_filter.py's get_sugar_trusted_sources() function
# Any changes to this list should be reflected in that function as well
#
# IMPORTANT: When updating this list, ensure that:
# 1. All source names are also added to get_sugar_trusted_sources() in source_filter.py
# 2. The source IDs match exactly with the Opoint API database
# 3. Both files remain synchronized to maintain consistency in the sugar news fetching pipeline
SUGAR_SOURCES = {
    # Sugar Industry Publications
    'sugar_industry_publications': [
        {'name': 'Food Processing', 'id': 171463},
        {'name': 'Sugar Producer', 'id': 124631}
    ],
    
    # Agricultural Commodity News Sources
    'agricultural_commodity_sources': [
        {'name': 'Argus Media', 'id': 82120},
        {'name': 'Fastmarkets', 'id': 30542},
        {'name': 'Ag Update', 'id': 335679},
        {'name': 'Agriinsite', 'id': 449222},
        {'name': 'Agronews', 'id': 256958},
        {'name': 'Tridge', 'id': 448815},
        {'name': 'ICE', 'id': 999},
    ],
    
    # Trade Publications Focused on Sugar and Sweeteners
    'trade_publications': [
        {'name': 'Food Navigator USA', 'id': 26214},
        {'name': 'Food Navigator', 'id': 241270},
        {'name': 'Benzinga', 'id': 23564},
        {'name': 'Yahoo! Finance', 'id': 3478},
        {'name': 'Business Insider', 'id': 12323},
        {'name': 'Investing', 'id': 10836},
        {'name': 'CNBC', 'id': 22991},
        {'name': 'Investing.com Brasil', 'id': 173901},
        {'name': 'Nasdaq', 'id': 913},
        {'name': 'Barchart', 'id': 124923},
        {'name': 'Market Screener', 'id': 37015},
        {'name': 'Barron\'s', 'id': 28875},
        {'name': 'Trading Economics', 'id': 213991},
        {'name': 'Chini Mandi', 'id': 442001},
        {'name': 'Globy', 'id': 464928},
        {'name': 'CME Group', 'id': 2737765}
    ],
    
    # Government and International Organizations
    'government_sources': [
        {'name': 'USDA', 'id': 15086},
        {'name': 'FAO', 'id': 53626}
    ]
}

# Flatten all sources for easier processing
ALL_SUGAR_SOURCES = []
ALL_SUGAR_SOURCE_NAMES = []
for category, sources in SUGAR_SOURCES.items():
    if isinstance(sources, dict):
        for region, region_sources in sources.items():
            ALL_SUGAR_SOURCES.extend(region_sources)
            ALL_SUGAR_SOURCE_NAMES.extend([source['name'] for source in region_sources])
    else:
        ALL_SUGAR_SOURCES.extend(sources)
        ALL_SUGAR_SOURCE_NAMES.extend([source['name'] for source in sources])

MEDIA_TOPIC_IDS = ['20000384','20000377','20000374', '20000386', '20000151', '20000210', '20000148','20000621'
,'20001129','20001131','20000324','20000369','20000366']

# Source category weights for dynamic quota allocation
# Higher weights mean more quota allocation
SOURCE_CATEGORY_WEIGHTS = {
    'sugar_industry_publications': 1.0,    # Highest priority - specialized sugar content
    'agricultural_commodity_sources': 0.8, # High priority - commodity focus
    'government_sources': 0.7,             # High priority - official data
    'trade_publications': 0.5              # Medium priority - broader financial news
}

# Source reliability scores (can be updated based on historical performance)
# These scores can be adjusted over time based on actual performance data
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

def calculate_source_quotas(max_articles, sources_config):
    """
    Calculate dynamic quota allocation for each source based on category weights and reliability scores.
    
    Args:
        max_articles (int): Maximum total articles to fetch
        sources_config (dict): Configuration of sources organized by category
        
    Returns:
        dict: Dictionary mapping source names to their allocated quotas
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
    """
    Get the category of a source based on its name.
    
    Args:
        source_name (str): Name of the source
        sources_config (dict): Configuration of sources organized by category
        
    Returns:
        str: Category name or 'unknown' if not found
    """
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


def generate_content_hash(title, text, source):
    """Generate a hash based on title, text, and source for deduplication"""
    content = f"{title}_{text}_{source}"
    return hashlib.md5(content.encode()).hexdigest()

def is_similar_content(title1, text1, source1, title2, text2, source2, threshold=0.9):
    """
    Check if two articles have similar content using fuzzy matching.
    Returns True if articles are similar, False otherwise.
    
    Args:
        title1, text1, source1: First article's title, text, and source
        title2, text2, source2: Second article's title, text, and source
        threshold: Similarity threshold (0.0 to 1.0)
    
    Returns:
        bool: True if articles are similar, False otherwise
    """
    # If sources are different, don't consider as duplicates even if content is similar
    if source1 != source2:
        return False
    
    # Combine title and text for comparison
    content1 = f"{title1} {text1}".lower().strip()
    content2 = f"{title2} {text2}".lower().strip()
    
    # If exact match, return True
    if content1 == content2:
        return True
    
    # Simple similarity check based on common words
    words1 = set(content1.split())
    words2 = set(content2.split())
    
    if not words1 or not words2:
        return False
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    similarity = len(intersection) / len(union)
    
    return similarity >= threshold

def normalize_and_filter_article(article, normalization_pipeline):
    """
    Normalize and filter a single article using the unified pipeline and triage logic.
    Returns structured result dict with asset information or None if not passed.
    """
    # Combine title and text for normalization
    raw_text = f"{article.get('title', '')}\n{article.get('text', '')}"
    normalized_text = normalization_pipeline.normalize(raw_text)

    # Clean HTML after normalization
    clean_text = clean_html(normalized_text)
    clean_title = clean_html(article.get('title', ''))

    # Apply triage filter (quality, keyword, context, pricing extraction)
    triage_result = triage_filter(clean_text, clean_title)

    # Determine asset based on triage filter result
    if triage_result.get("passed", False):
        asset = "Sugar"
    else:
        asset = "General"

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
            asset
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
        "raw_article": article,
        "asset": asset,
        "triage_passed": triage_result.get("passed", False),
        "triage_reason": triage_result.get("reason", "")
    }
    return result

def fetch_sugar_articles_for_period(api_key, start_date, end_date, topic_ids, max_articles=30000, normalization_pipeline=None):
    """
    Fetch and process sugar news articles for a given period and topic IDs.
    Returns a DataFrame of structured, filtered articles.
    
    Args:
        api_key: Opoint API key
        start_date: Start date for fetching articles
        end_date: End date for fetching articles
        topic_ids: List of topic IDs to search
        max_articles: Maximum number of articles to fetch
        normalization_pipeline: Language normalization pipeline
    """
    global request_counter
    with request_lock:
        request_counter += 1
        current_request_id = request_counter
    
    logger.info(f"[Request-{current_request_id}] Starting fetch for {start_date.date()} to {end_date.date()}, topics: {topic_ids}")
    
    # Acquire semaphore to limit concurrent API requests
    logger.debug(f"[Request-{current_request_id}] Acquiring semaphore for API request")
    acquired = active_requests.acquire(timeout=60)  # Wait up to 60 seconds for a slot
    if not acquired:
        logger.error(f"[Request-{current_request_id}] Timeout waiting for semaphore - resource exhaustion!")
        raise Exception("Timeout waiting for available API request slot")
    
    try:
        logger.debug(f"[Request-{current_request_id}] Semaphore acquired, creating API instance")
        api = OpointAPI(api_key=api_key)
        
        # Build search query for sugar sources
        logger.debug(f"[Request-{current_request_id}] Building search queries")
        sugar_search_query = build_search_query(
            topic_ids,
            SUGAR_CONFIG['person_entities'],
            SUGAR_CONFIG['company_entities'],
            ALL_SUGAR_SOURCE_NAMES
        )

        # Build search query for non-sugar sources (without source filtering)
        non_sugar_search_query = build_search_query(
            topic_ids,
            SUGAR_CONFIG['person_entities'],
            SUGAR_CONFIG['company_entities'],
            None  # No source filtering for non-sugar sources
        )

        logger.info(f"[Request-{current_request_id}] Fetching articles from {start_date.date()} to {end_date.date()}")
        print(f"Fetching articles from {start_date.date()} to {end_date.date()}")
        print(f"Processing sugar and non-sugar sources separately")
        
        # Calculate dynamic quota allocation for sugar sources
        sugar_source_quotas = calculate_source_quotas(max_articles // 2, SUGAR_SOURCES)  # Use half of max_articles for sugar sources
        
        # Log quota allocation
        print(f"\n=== DYNAMIC QUOTA ALLOCATION ===")
        print(f"Allocating quotas for {len(sugar_source_quotas)} sugar sources:")
        total_sugar_quota = 0
        for source, quota in sugar_source_quotas.items():
            category = get_source_category(source, SUGAR_SOURCES)
            reliability = SOURCE_RELIABILITY_SCORES.get(source, 0.5)
            print(f"  - {source} ({category}): {quota} articles (reliability: {reliability:.2f})")
            total_sugar_quota += quota
        print(f"Total sugar sources quota: {total_sugar_quota} articles")
        
        # === STEP 1: Fetch articles from sugar sources ===
        logger.debug(f"[Request-{current_request_id}] Starting STEP 1: Fetching from sugar sources")
        print(f"\n=== STEP 1: Fetching from sugar sources ===")
        print(f"Filtering for {len(ALL_SUGAR_SOURCES)} sugar-specific sources with dynamic quotas")
        
        sugar_results = []
        
        # Process each sugar source separately to avoid overwhelming the API
        processed_sources = set()  # Track which sources we've already processed
        for category, sources in SUGAR_SOURCES.items():
            if isinstance(sources, dict):
                # Handle regional sources
                for region, region_sources in sources.items():
                    logger.debug(f"[Request-{current_request_id}] Fetching from {region} sources: {[s['name'] for s in region_sources]}")
                    print(f"  Fetching from {region} sources: {[s['name'] for s in region_sources]}")
                    for source in region_sources:
                        # Skip if we've already processed this source
                        if source['name'] in processed_sources:
                            logger.debug(f"[Request-{current_request_id}] Skipping already processed source: {source['name']}")
                            continue
                        processed_sources.add(source['name'])
                        
                        # Get dynamic quota for this source
                        source_quota = sugar_source_quotas.get(source['name'], 10)  # Default to 10 if not found
                        
                        try:
                            logger.debug(f"[Request-{current_request_id}] Making API call to {source['name']} with quota {source_quota}")
                            # Use source ID directly with site_id parameter
                            if source['id']:
                                results = api.search_articles(
                                    site_id=str(source['id']),
                                    search_text=sugar_search_query,
                                    num_articles=min(source_quota, 50),  # Use dynamic quota, cap at 50 to prevent overload
                                    min_score=0.77,
                                    start_date=start_date,
                                    end_date=end_date,
                                    timeout=30  # 30 second timeout
                                )
                            else:
                                # Fallback to source name if ID is not available
                                results = api.search_site_and_articles(
                                    site_name=None,
                                    search_text=sugar_search_query,
                                    source=source['name'],
                                    num_articles=min(source_quota, 50),  # Use dynamic quota, cap at 50 to prevent overload
                                    min_score=0.77,
                                    start_date=start_date,
                                    end_date=end_date,
                                    timeout=30  # 30 second timeout
                                )
                            if not results.empty:
                                sugar_results.append(results)
                                logger.debug(f"[Request-{current_request_id}] Found {len(results)} articles from {source['name']}")
                                print(f"    Found {len(results)} articles from {source['name']} (quota: {source_quota})")
                        except Exception as e:
                            logger.error(f"[Request-{current_request_id}] Error fetching from {source['name']}: {str(e)}")
                            print(f"    Error fetching from {source['name']}: {str(e)}")
            else:
                # Handle flat source lists
                logger.debug(f"[Request-{current_request_id}] Fetching from {category}: {[s['name'] for s in sources]}")
                print(f"  Fetching from {category}: {[s['name'] for s in sources]}")
                for source in sources:
                    # Skip if we've already processed this source
                    if source['name'] in processed_sources:
                        logger.debug(f"[Request-{current_request_id}] Skipping already processed source: {source['name']}")
                        continue
                    processed_sources.add(source['name'])
                    
                    # Get dynamic quota for this source
                    source_quota = sugar_source_quotas.get(source['name'], 10)  # Default to 10 if not found
                    
                    try:
                        logger.debug(f"[Request-{current_request_id}] Making API call to {source['name']} with quota {source_quota}")
                        # Use source ID directly with site_id parameter
                        if source['id']:
                            results = api.search_articles(
                                site_id=str(source['id']),
                                search_text=sugar_search_query,
                                num_articles=min(source_quota, 50),  # Use dynamic quota, cap at 50 to prevent overload
                                min_score=0.77,
                                start_date=start_date,
                                end_date=end_date,
                                timeout=30  # 30 second timeout
                            )
                        else:
                            # Fallback to source name if ID is not available
                            results = api.search_site_and_articles(
                                site_name=None,
                                search_text=sugar_search_query,
                                source=source['name'],
                                num_articles=min(source_quota, 50),  # Use dynamic quota, cap at 50 to prevent overload
                                min_score=0.77,
                                start_date=start_date,
                                end_date=end_date,
                                timeout=30  # 30 second timeout
                            )
                        if not results.empty:
                            sugar_results.append(results)
                            logger.debug(f"[Request-{current_request_id}] Found {len(results)} articles from {source['name']}")
                            print(f"    Found {len(results)} articles from {source['name']} (quota: {source_quota})")
                    except Exception as e:
                        logger.error(f"[Request-{current_request_id}] Error fetching from {source['name']}: {str(e)}")
                        print(f"    Error fetching from {source['name']}: {str(e)}")
        
        # Combine sugar results
        if sugar_results:
            sugar_df = pd.concat(sugar_results, ignore_index=True)
            logger.info(f"[Request-{current_request_id}] Total articles from sugar sources: {len(sugar_df)}")
            print(f"Total articles from sugar sources: {len(sugar_df)}")
        else:
            sugar_df = pd.DataFrame()
            logger.info(f"[Request-{current_request_id}] No articles found from sugar sources")
            print("No articles found from sugar sources")

        # === STEP 2: Fetch articles from non-sugar sources ===
        logger.debug(f"[Request-{current_request_id}] Starting STEP 2: Fetching from non-sugar sources")
        print(f"\n=== STEP 2: Fetching from non-sugar sources ===")
        
        # Calculate quota for non-sugar sources (use remaining half of max_articles)
        non_sugar_quota = max_articles // 2
        print(f"Allocating {non_sugar_quota} articles for non-sugar sources")
        
        try:
            logger.debug(f"[Request-{current_request_id}] Making API call for non-sugar sources with quota {non_sugar_quota}")
            non_sugar_results = api.search_articles(
                search_text=non_sugar_search_query,
                num_articles=min(non_sugar_quota, 100),  # Use calculated quota, cap at 100 to prevent overload
                min_score=0.77,
                start_date=start_date,
                end_date=end_date,
                timeout=30  # 30 second timeout
            )
            
            if not non_sugar_results.empty:
                logger.info(f"[Request-{current_request_id}] Found {len(non_sugar_results)} articles from non-sugar sources")
                print(f"Found {len(non_sugar_results)} articles from non-sugar sources (quota: {non_sugar_quota})")
                # Exclude articles from sugar-specific sources to avoid duplication
                non_sugar_df = non_sugar_results[~non_sugar_results['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)].copy()
                logger.info(f"[Request-{current_request_id}] After excluding sugar sources: {len(non_sugar_df)} articles")
                print(f"After excluding sugar sources: {len(non_sugar_df)} articles")
            else:
                non_sugar_df = pd.DataFrame()
                logger.info(f"[Request-{current_request_id}] No articles found from non-sugar sources")
                print("No articles found from non-sugar sources")
        except Exception as e:
            logger.error(f"[Request-{current_request_id}] Error fetching from non-sugar sources: {str(e)}")
            print(f"Error fetching from non-sugar sources: {str(e)}")
            non_sugar_df = pd.DataFrame()

        # === STEP 3: Combine results from both sources ===
        if sugar_df.empty and non_sugar_df.empty:
            logger.info(f"[Request-{current_request_id}] No articles found for sugar in {start_date.date()}")
            print(f"No articles found for sugar in {start_date.date()}")
            return pd.DataFrame()
        
        # Combine both dataframes
        all_results = pd.concat([sugar_df, non_sugar_df], ignore_index=True)
        logger.info(f"[Request-{current_request_id}] Total articles from all sources: {len(all_results)}")
        print(f"Total articles from all sources: {len(all_results)}")

        # === STEP 4: Apply normalization and triage pipeline to all articles ===
        logger.debug(f"[Request-{current_request_id}] Starting STEP 4: Applying normalization and triage pipeline")
        print(f"\n=== STEP 4: Applying normalization and triage pipeline to all articles ===")
        
        structured_articles = []
        seen_content_hashes = set()
        triage_passed_count = 0
        triage_failed_count = 0
        
        # Process all articles through the triage filter with memory-efficient deduplication
        # Limit the number of articles stored for similarity checking to prevent memory issues
        max_similarity_check = 1000  # Only check similarity against the last 1000 articles
        processed_articles = []  # Store processed articles for similarity checking
        
        for _, article in all_results.iterrows():
            # Generate content hash for deduplication
            title = article.get('title', '')
            text = article.get('text', '')
            source = article.get('site_name', '') or article.get('source_name', '')
            content_hash = generate_content_hash(title, text, source)
            
            # Skip if we've already seen this exact content
            if content_hash in seen_content_hashes:
                continue
                
            # Check for similar content with recently processed articles (limited to prevent memory issues)
            is_duplicate = False
            # Only check against the most recent articles to limit memory usage
            recent_articles = processed_articles[-max_similarity_check:] if len(processed_articles) > max_similarity_check else processed_articles
            
            for processed_article in recent_articles:
                if is_similar_content(
                    title, text, source,
                    processed_article['title'], processed_article['text'], processed_article['source']
                ):
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
                
            seen_content_hashes.add(content_hash)
            
            # Store article info for similarity checking (limit size to prevent memory issues)
            processed_articles.append({
                'title': title,
                'text': text,
                'source': source
            })
            
            # Periodically clean up old articles to prevent memory buildup
            if len(processed_articles) > max_similarity_check * 2:
                processed_articles = processed_articles[-max_similarity_check:]
            
            result = normalize_and_filter_article(article, normalization_pipeline)
            if result:
                # Add content hash to result for tracking
                result['content_hash'] = content_hash
                structured_articles.append(result)
                
                # Track triage filter results
                if result.get('triage_passed', False):
                    triage_passed_count += 1
                else:
                    triage_failed_count += 1

        if not structured_articles:
            logger.info(f"[Request-{current_request_id}] No articles processed for sugar in {start_date.date()}")
            print(f"No articles processed for sugar in {start_date.date()}")
            return pd.DataFrame()

        # Log triage filter statistics
        print(f"Triage filter results for {start_date.date()}:")
        print(f"  - Passed: {triage_passed_count} articles (asset='Sugar')")
        print(f"  - Failed: {triage_failed_count} articles (asset='General')")
        print(f"  - Total processed: {len(structured_articles)} articles")

        # Convert to DataFrame
        df_structured = pd.DataFrame(structured_articles)

        # Apply source filtering to all articles (including sugar sources)
        logger.debug(f"[Request-{current_request_id}] Starting STEP 5: Applying source filtering to all articles")
        print(f"\n=== STEP 5: Applying source filtering to all articles ===")
        df_structured = filter_trusted_sources(df_structured, verbose=True)

        # Report deduplication statistics
        original_count = len(all_results)
        final_count = len(df_structured)
        duplicates_removed = original_count - final_count
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate articles based on content matching")
            print(f"Kept {final_count} unique articles from {original_count} total articles")

        # Log source distribution with special attention to sugar sources
        if not df_structured.empty:
            sugar_source_articles = df_structured[df_structured['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)]
            non_sugar_source_articles = df_structured[~df_structured['site_name'].isin(ALL_SUGAR_SOURCE_NAMES)]
            
            sugar_source_count = len(sugar_source_articles)
            non_sugar_source_count = len(non_sugar_source_articles)
            
            print(f"\n=== SOURCE DISTRIBUTION ANALYSIS ===")
            print(f"Total articles: {len(df_structured)}")
            print(f"  - Sugar sources: {sugar_source_count} articles")
            print(f"  - Non-sugar sources: {non_sugar_source_count} articles")
            
            # Special logging for sugar sources
            if sugar_source_count > 0:
                print(f"\n=== SUGAR SOURCES PRIORITY ANALYSIS ===")
                print(f"Sugar sources processed and passed all filters:")
                
                # Group by sugar source name
                sugar_sources_grouped = sugar_source_articles.groupby('site_name').size().sort_values(ascending=False)
                for source, count in sugar_sources_grouped.items():
                    # Calculate percentage of sugar articles that passed triage for this source
                    passed_triage = len(sugar_source_articles[(sugar_source_articles['site_name'] == source) &
                                                             (sugar_source_articles['asset'] == 'Sugar')])
                    pass_rate = (passed_triage / count) * 100 if count > 0 else 0
                    
                    # Get quota and reliability information for this source
                    allocated_quota = sugar_source_quotas.get(source, 0)
                    reliability = SOURCE_RELIABILITY_SCORES.get(source, 0.5)
                    category = get_source_category(source, SUGAR_SOURCES)
                    
                    # Calculate quota utilization
                    quota_utilization = (count / allocated_quota * 100) if allocated_quota > 0 else 0
                    
                    print(f"  - {source} ({category}): {count} articles ({pass_rate:.1f}% passed triage)")
                    print(f"    Allocated quota: {allocated_quota}, Utilization: {quota_utilization:.1f}%, Reliability: {reliability:.2f}")
                
                # Overall sugar source statistics
                total_sugar_passed = len(sugar_source_articles[sugar_source_articles['asset'] == 'Sugar'])
                overall_sugar_pass_rate = (total_sugar_passed / sugar_source_count) * 100 if sugar_source_count > 0 else 0
                
                # Calculate overall quota utilization
                total_allocated_quota = sum(sugar_source_quotas.values())
                overall_quota_utilization = (sugar_source_count / total_allocated_quota * 100) if total_allocated_quota > 0 else 0
                
                print(f"\nOverall sugar source performance:")
                print(f"  - Total sugar articles: {sugar_source_count}")
                print(f"  - Passed triage (asset='Sugar'): {total_sugar_passed}")
                print(f"  - Overall pass rate: {overall_sugar_pass_rate:.1f}%")
                print(f"  - Total allocated quota: {total_allocated_quota}")
                print(f"  - Overall quota utilization: {overall_quota_utilization:.1f}%")
                
                # Weekly interval analysis
                week_start = start_date.strftime("%Y-%m-%d")
                week_end = end_date.strftime("%Y-%m-%d")
                print(f"\nWeekly interval analysis ({week_start} to {week_end}):")
                print(f"  - Articles per day: {sugar_source_count / 7:.1f}")
                print(f"  - High-value sources (pass rate > 70%): {len([s for s in sugar_sources_grouped.index if (sugar_source_articles[(sugar_source_articles['site_name'] == s) & (sugar_source_articles['asset'] == 'Sugar')].shape[0] / sugar_sources_grouped[s] * 100) > 70])}")
            
            # Log top non-sugar sources for comparison
            if non_sugar_source_count > 0:
                print(f"\n=== TOP NON-SUGAR SOURCES ===")
                non_sugar_sources_grouped = non_sugar_source_articles.groupby('site_name').size().sort_values(ascending=False).head(5)
                for source, count in non_sugar_sources_grouped.items():
                    passed_triage = len(non_sugar_source_articles[(non_sugar_source_articles['site_name'] == source) &
                                                               (non_sugar_source_articles['asset'] == 'Sugar')])
                    pass_rate = (passed_triage / count) * 100 if count > 0 else 0
                    print(f"  - {source}: {count} articles ({pass_rate:.1f}% passed triage)")

        logger.info(f"[Request-{current_request_id}] Successfully completed processing, returning {len(df_structured)} articles")
        return df_structured
    
    except Exception as e:
        logger.error(f"[Request-{current_request_id}] Exception in fetch_sugar_articles_for_period: {str(e)}")
        raise
    finally:
        # Always release the semaphore
        active_requests.release()
        logger.debug(f"[Request-{current_request_id}] Semaphore released")

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

def main():
    parser = argparse.ArgumentParser(description="Fetch and filter sugar news articles with unified logic")
    parser.add_argument('--dry-run', action='store_true', help='Print what would be done without executing')
    parser.add_argument('--max-workers', type=int, default=2, help='Maximum number of concurrent workers (default: 2)')
    parser.add_argument('--weeks-back', type=int, default=48, help='Number of weeks back to fetch (default: 48, approx 12 months)')
    parser.add_argument('--max-articles', type=int, default=1000, help='Maximum articles per request (default: 1000)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint if available')
    parser.add_argument('--checkpoint-dir', type=str, default='./checkpoints', help='Directory for storing checkpoints (default: ./checkpoints)')
    args = parser.parse_args()

    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        print("Error: OPOINT_API_KEY environment variable not found")
        return

    date_ranges = generate_date_ranges(args.weeks_back)
    total_tasks = len(date_ranges) * len(MEDIA_TOPIC_IDS)
    logger.info(f"Starting sugar news fetch across {len(date_ranges)} weeks")
    logger.info(f"Using {len(MEDIA_TOPIC_IDS)} media topic IDs: {', '.join(MEDIA_TOPIC_IDS)}")
    logger.warning(f"TOTAL TASKS TO PROCESS: {total_tasks} - This may cause resource exhaustion!")
    logger.info(f"Max workers: {args.max_workers}")
    
    print(f"Starting sugar news fetch across {len(date_ranges)} weeks")
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

    # Check for resume option and load intermediate results if available
    if args.resume:
        logger.info(f"Resume mode enabled. Loading intermediate results from {args.checkpoint_dir}")
        loaded_results = load_intermediate_results(args.checkpoint_dir)
        if loaded_results:
            all_structured = loaded_results
            total_saved = sum(len(df) for df in all_structured)
            logger.info(f"Loaded {len(all_structured)} dataframes with {total_saved} articles from checkpoints")
            print(f"Resumed with {len(all_structured)} dataframes and {total_saved} articles from checkpoints")
        else:
            logger.info("No checkpoints found, starting fresh")
            print("No checkpoints found, starting fresh")

    # Global exception handler to ensure intermediate results are preserved
    try:

        logger.info("Starting BATCHED ThreadPoolExecutor for task processing to prevent resource exhaustion")
        completed_tasks = 0
        failed_tasks = 0
        
        # Process tasks in smaller batches to prevent resource exhaustion
        BATCH_SIZE = 10  # Reduce batch size to 10 tasks at a time to prevent memory overload
        all_tasks = []
        
        # Create list of all tasks
        for start_date, end_date in date_ranges:
            for topic_id in MEDIA_TOPIC_IDS:
                all_tasks.append((start_date, end_date, topic_id))
        
        logger.info(f"Processing {len(all_tasks)} tasks in batches of {BATCH_SIZE}")
        
        # Determine starting batch based on loaded results
        start_batch = 0
        if args.resume and all_structured:
            # Estimate which batch we should start from based on loaded data
            # This is a simple heuristic - in a production system, you'd want more sophisticated tracking
            estimated_completed_tasks = len(all_structured)
            start_batch = (estimated_completed_tasks // BATCH_SIZE) * BATCH_SIZE
            logger.info(f"Estimated starting batch: {start_batch // BATCH_SIZE + 1} (task {start_batch + 1})")
            print(f"Resuming from batch {start_batch // BATCH_SIZE + 1}")
        
        # Process tasks in batches
        for batch_start in range(start_batch, len(all_tasks), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(all_tasks))
            current_batch = all_tasks[batch_start:batch_end]
            batch_number = batch_start // BATCH_SIZE + 1
            
            logger.info(f"Processing batch {batch_number}: tasks {batch_start+1} to {batch_end}")
            print(f"Processing batch {batch_number}: tasks {batch_start+1} to {batch_end}")
            
            with ThreadPoolExecutor(max_workers=min(args.max_workers, 2)) as executor:  # Further limit workers per batch to prevent overload
                future_to_task = {}
                
                for task_idx, (start_date, end_date, topic_id) in enumerate(current_batch):
                    global_task_idx = batch_start + task_idx + 1
                    logger.debug(f"Submitting task {global_task_idx}/{len(all_tasks)}: {start_date.date()} to {end_date.date()}, topic: {topic_id}")
                    
                    future = executor.submit(
                        fetch_sugar_articles_for_period,
                        api_key, start_date, end_date, [topic_id], args.max_articles, normalization_pipeline
                    )
                    future_to_task[future] = (start_date, end_date, topic_id)

                logger.info(f"Batch {batch_number} submitted. Waiting for completion...")
                
                for future in as_completed(future_to_task):
                    start_date, end_date, topic_id = future_to_task[future]
                    try:
                        logger.debug(f"Processing completed task: {start_date.date()} topic:{topic_id}")
                        
                        # Check memory usage before processing result
                        if not check_memory_usage(max_memory_mb=3000):  # Lower threshold for safety
                            logger.warning("Memory usage too high, running cleanup...")
                            cleanup_memory()
                            time.sleep(2)  # Give system time to free up memory
                        
                        df_structured = future.result()
                        if not df_structured.empty:
                            all_structured.append(df_structured)
                            total_saved += len(df_structured)
                            logger.debug(f"Task completed successfully: {start_date.date()} topic:{topic_id}, articles: {len(df_structured)}")
                        else:
                            logger.debug(f"Task completed with no results: {start_date.date()} topic:{topic_id}")
                        completed_tasks += 1
                        time.sleep(0.5)  # Longer delay to prevent overwhelming the system
                        
                        # Periodic memory cleanup
                        if completed_tasks % 5 == 0:
                            cleanup_memory()
                            
                    except Exception as e:
                        failed_tasks += 1
                        logger.error(f"Task failed for {start_date.date()} topic:{topic_id}: {str(e)}")
                        print(f"Task failed for {start_date.date()} topic:{topic_id}: {str(e)}")
                
                logger.info(f"Batch {batch_number} completed. Successful: {completed_tasks}, Failed: {failed_tasks}")
            
            # Save intermediate results after each batch for recovery
            if not args.dry_run:
                save_success = save_intermediate_results(all_structured, batch_number, args.checkpoint_dir)
                if save_success:
                    logger.info(f"Successfully saved intermediate results after batch {batch_number}")
                    print(f"Saved intermediate results after batch {batch_number}")
                else:
                    logger.warning(f"Failed to save intermediate results after batch {batch_number}")
                    print(f"Warning: Failed to save intermediate results after batch {batch_number}")
            
            # Add a longer delay between batches to allow system resources to free up
            if batch_end < len(all_tasks):
                logger.info(f"Pausing for 10 seconds between batches to free up system resources...")
                print(f"Pausing for 10 seconds between batches...")
                
                # Check memory usage and run cleanup if needed
                if not check_memory_usage(max_memory_mb=2000):  # Even lower threshold between batches
                    logger.warning("Memory usage high between batches, running extensive cleanup...")
                    cleanup_memory()
                    time.sleep(5)  # Additional time for cleanup
                
                time.sleep(10)
        
        logger.info(f"All task execution completed. Successful: {completed_tasks}, Failed: {failed_tasks}")

    # Concatenate all results
        if all_structured:
            final_df = pd.concat(all_structured, ignore_index=True)
            
            # Log overall statistics
            total_articles = len(final_df)
            sugar_articles = len(final_df[final_df['asset'] == 'Sugar'])
            general_articles = len(final_df[final_df['asset'] == 'General'])
            
            print(f"\n=== OVERALL STATISTICS ===")
            print(f"Total articles processed: {total_articles}")
            print(f"Sugar articles (passed triage): {sugar_articles}")
            print(f"General articles (failed triage): {general_articles}")
            
            # Save to database
            search_metadata = {
                'topic_ids': MEDIA_TOPIC_IDS,
                'keywords_main': SUGAR_CONFIG['keywords_main'],
                'keywords_exclusion': SUGAR_CONFIG['keywords_exclusion'],
                'keywords_context_zones': SUGAR_CONFIG['keywords_context_zones'],
                'company_entities': SUGAR_CONFIG['company_entities'],
                'government_entities': SUGAR_CONFIG['government_entities'],
                'person_entities': SUGAR_CONFIG['person_entities'],
                'search_period': f"{date_ranges[-1][0].date()} to {date_ranges[0][1].date()}"
            }
            
            # Save only articles that passed the triage filter (asset='Sugar')
            sugar_only_df = final_df[final_df['asset'] == 'Sugar'].copy()
            
            if not args.dry_run:
                try:
                    saved_count = save_to_database(sugar_only_df, search_metadata, 'Sugar')
                    print(f"Saved {saved_count} articles to database")
                    
                    # Clean up checkpoint files after successful database save
                    if saved_count > 0:
                        cleanup_success = cleanup_checkpoint_files(args.checkpoint_dir)
                        if cleanup_success:
                            logger.info("Successfully cleaned up checkpoint files after successful completion")
                            print("Cleaned up checkpoint files after successful completion")
                        else:
                            logger.warning("Failed to cleanup checkpoint files")
                            print("Warning: Failed to cleanup checkpoint files")
                    
                    # Log breakdown by asset type
                    if saved_count > 0:
                        sugar_saved = len(sugar_only_df)
                        general_saved = len(final_df[(final_df['asset'] == 'General')])
                        print(f"Breakdown by asset type:")
                        print(f"  - Sugar articles saved: {sugar_saved}")
                        print(f"  - General articles (not saved): {general_saved}")
                except Exception as e:
                    logger.error(f"Failed to save to database: {str(e)}")
                    print(f"Error: Failed to save to database: {str(e)}")
                    print("Intermediate results have been preserved for recovery")
                    print(f"You can resume using: --resume --checkpoint-dir {args.checkpoint_dir}")
            else:
                # Dry run - don't save to database or clean up checkpoints
                print("DRY RUN: Would save to database")
                sugar_saved = len(sugar_only_df)
                general_saved = len(final_df[(final_df['asset'] == 'General')])
                print(f"Breakdown by asset type:")
                print(f"  - Sugar articles would be saved: {sugar_saved}")
                print(f"  - General articles (not saved): {general_saved}")
        else:
            print("No articles processed.")

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n=== SUGAR NEWS FETCH COMPLETED ===")
        print(f"Total articles saved: {total_saved}")
        print(f"Total duration: {duration}")
        print(f"Average time per task: {duration.total_seconds() / total_tasks:.2f} seconds")
        print(f"Date range: {date_ranges[-1][0].date()} to {date_ranges[0][1].date()}")
        print(f"Processed {len(date_ranges)} weekly intervals")
        
        # Calculate and display weekly statistics
        if len(date_ranges) > 0:
            total_weeks = len(date_ranges)
            avg_articles_per_week = total_saved / total_weeks if total_weeks > 0 else 0
            print(f"Average articles per week: {avg_articles_per_week:.1f}")
            
            # Calculate date span in weeks
            date_span_weeks = (date_ranges[0][1] - date_ranges[-1][0]).days / 7
            print(f"Date span: {date_span_weeks:.1f} weeks")
            
            # Display dynamic quota allocation summary
            print(f"\n=== DYNAMIC QUOTA ALLOCATION SUMMARY ===")
            print(f"Source category weights:")
            for category, weight in SOURCE_CATEGORY_WEIGHTS.items():
                print(f"  - {category}: {weight}")
            
            print(f"\nTop sources by reliability score:")
            top_sources = sorted(SOURCE_RELIABILITY_SCORES.items(), key=lambda x: x[1], reverse=True)[:5]
            for source, reliability in top_sources:
                category = get_source_category(source, SUGAR_SOURCES)
                print(f"  - {source} ({category}): {reliability:.2f}")
    
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}")
        print(f"Fatal error: {str(e)}")
        print("Intermediate results have been preserved for recovery")
        print(f"You can resume using: --resume --checkpoint-dir {args.checkpoint_dir}")
        return 1
    
    finally:
        # This block always executes, whether there was an exception or not
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Process ended at {end_time}, total duration: {duration}")
        
        # If we're exiting with an error or interruption, ensure intermediate results are preserved
        if 'failed_tasks' in locals() and failed_tasks > 0:
            logger.warning(f"Process completed with {failed_tasks} failed tasks")
            print(f"Warning: Process completed with {failed_tasks} failed tasks")
            print("Intermediate results have been preserved for recovery")
            print(f"You can resume using: --resume --checkpoint-dir {args.checkpoint_dir}")

if __name__ == "__main__":
    main()
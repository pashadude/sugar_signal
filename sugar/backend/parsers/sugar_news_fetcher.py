#!/usr/bin/env python
"""
Sugar News Fetcher with Simplified Filtering Logic

- Integrates normalization pipeline (translation, typo correction, slang mapping, punctuation normalization, edge case handling)
- Applies simplified keyword-based filtering (main sugar keywords only) with multilingual support
- Implements simplified triage logic focused on sugar-related content only
- EXCLUSIVELY queries 27 predefined sugar sources with matching MEDIA_IDs
- All quota allocated to the 27 predefined sugar sources only
- Context zones, structured pricing, and name-entity recognition are used only for metadata extraction
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
import sqlite3
from typing import List, Tuple, Dict, Any
# Try to import psutil for memory monitoring, but make it optional
try:
    import psutil  # For memory monitoring
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Silently disable memory monitoring if psutil is not available
    pass

import gc  # For garbage collection
import tiktoken  # For token counting

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
        # Silently continue if psutil is not available
        pass
        return 0

def check_memory_usage(max_memory_mb=4000):
    """Check if memory usage is within limits, return True if OK"""
    if PSUTIL_AVAILABLE:
        current_memory = get_memory_usage()
        # Silently check memory usage
        pass
        if current_memory > max_memory_mb:
            # Silently handle high memory usage
            pass
            return False
        return True
    else:
        # Fallback: always return True when psutil is not available
        # Silently skip memory usage check if psutil is not available
        pass
        return True

def cleanup_memory():
    """Force garbage collection and clean up memory"""
    # Silently run garbage collection
    pass
    gc.collect()

def save_checkpoint(checkpoint_data, checkpoint_file):
    """Save checkpoint data to file for recovery in case of failure"""
    try:
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        # Silently save checkpoint
        pass
        return True
    except Exception as e:
        # Silently handle checkpoint save failure
        pass
        return False

def load_checkpoint(checkpoint_file):
    """Load checkpoint data from file for recovery"""
    try:
        if not os.path.exists(checkpoint_file):
            # Silently handle missing checkpoint file
            pass
            return None
        
        with open(checkpoint_file, 'rb') as f:
            checkpoint_data = pickle.load(f)
        # Silently load checkpoint
        pass
        return checkpoint_data
    except Exception as e:
        # Silently handle checkpoint load failure
        pass
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
        
        # Silently save intermediate results
        pass
        return True
    except Exception as e:
        # Silently handle intermediate results save failure
        pass
        return False

def load_intermediate_results(checkpoint_dir):
    """Load all intermediate results from checkpoint directory"""
    try:
        if not os.path.exists(checkpoint_dir):
            # Silently handle missing checkpoint directory
            pass
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
                # Silently load intermediate results
                pass
            except Exception as e:
                # Silently handle intermediate results load failure
                pass
        
        return all_results
    except Exception as e:
        # Silently handle intermediate results load failure
        pass
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
                # Silently remove checkpoint file
                pass
            except Exception as e:
                # Silently handle checkpoint file removal failure
                pass
        
        # Try to remove the directory if it's empty
        try:
            if not os.listdir(checkpoint_dir):
                os.rmdir(checkpoint_dir)
                # Silently remove empty checkpoint directory
                pass
        except Exception as e:
            # Silently handle checkpoint directory removal failure
            pass
        
        return True
    except Exception as e:
        # Silently handle checkpoint cleanup failure
        pass
        return False

class ProcessedDatesTracker:
    """
    Thread-safe tracker for processed date ranges to prevent duplicate processing.
    
    This class maintains a SQLite database of processed date ranges and provides
    methods to check if dates have already been processed and to mark dates as processed.
    """
    
    def __init__(self, db_path="processed_dates.db"):
        """Initialize the tracker with a database path"""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for tracking processed dates"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table for processed date ranges
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_date_ranges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    processing_mode TEXT NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(start_date, end_date, processing_mode)
                )
            ''')
            
            # Create table for individual processed dates (for more granular tracking)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_dates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    processing_mode TEXT NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, processing_mode)
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def is_date_range_processed(self, start_date, end_date, processing_mode):
        """
        Check if a date range has already been processed.
        
        Args:
            start_date (datetime): Start date of the range
            end_date (datetime): End date of the range
            processing_mode (str): Processing mode ('weekly' or 'monthly')
            
        Returns:
            bool: True if the date range has been processed, False otherwise
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for exact match
            cursor.execute('''
                SELECT COUNT(*) FROM processed_date_ranges
                WHERE start_date = ? AND end_date = ? AND processing_mode = ?
            ''', (start_date.isoformat(), end_date.isoformat(), processing_mode))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
    
    def is_date_processed(self, date, processing_mode):
        """
        Check if a specific date has been processed.
        
        Args:
            date (datetime): Date to check
            processing_mode (str): Processing mode ('weekly' or 'monthly')
            
        Returns:
            bool: True if the date has been processed, False otherwise
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM processed_dates
                WHERE date = ? AND processing_mode = ?
            ''', (date.isoformat(), processing_mode))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
    
    def mark_date_range_processed(self, start_date, end_date, processing_mode):
        """
        Mark a date range as processed.
        
        Args:
            start_date (datetime): Start date of the range
            end_date (datetime): End date of the range
            processing_mode (str): Processing mode ('weekly' or 'monthly')
            
        Returns:
            bool: True if successfully marked, False otherwise
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Mark the date range as processed
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_date_ranges
                    (start_date, end_date, processing_mode)
                    VALUES (?, ?, ?)
                ''', (start_date.isoformat(), end_date.isoformat(), processing_mode))
                
                # Also mark all individual dates in the range as processed
                current_date = start_date
                while current_date <= end_date:
                    cursor.execute('''
                        INSERT OR REPLACE INTO processed_dates
                        (date, processing_mode)
                        VALUES (?, ?)
                    ''', (current_date.isoformat(), processing_mode))
                    current_date += timedelta(days=1)
                
                conn.commit()
                conn.close()
                return True
                
            except Exception as e:
                # Silently handle date range marking failure
                pass
                return False
    
    def get_processed_date_ranges(self, processing_mode=None, limit=None):
        """
        Get list of processed date ranges.
        
        Args:
            processing_mode (str, optional): Filter by processing mode
            limit (int, optional): Limit number of results
            
        Returns:
            list: List of tuples (start_date, end_date, processing_mode, processed_at)
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if processing_mode:
                cursor.execute('''
                    SELECT start_date, end_date, processing_mode, processed_at
                    FROM processed_date_ranges
                    WHERE processing_mode = ?
                    ORDER BY processed_at DESC
                    LIMIT ?
                ''', (processing_mode, limit or 1000))
            else:
                cursor.execute('''
                    SELECT start_date, end_date, processing_mode, processed_at
                    FROM processed_date_ranges
                    ORDER BY processed_at DESC
                    LIMIT ?
                ''', (limit or 1000,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
    
    def get_processed_dates(self, processing_mode=None, limit=None):
        """
        Get list of processed individual dates.
        
        Args:
            processing_mode (str, optional): Filter by processing mode
            limit (int, optional): Limit number of results
            
        Returns:
            list: List of tuples (date, processing_mode, processed_at)
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if processing_mode:
                cursor.execute('''
                    SELECT date, processing_mode, processed_at
                    FROM processed_dates
                    WHERE processing_mode = ?
                    ORDER BY processed_at DESC
                    LIMIT ?
                ''', (processing_mode, limit or 1000))
            else:
                cursor.execute('''
                    SELECT date, processing_mode, processed_at
                    FROM processed_dates
                    ORDER BY processed_at DESC
                    LIMIT ?
                ''', (limit or 1000,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
    
    def check_overlap_with_processed_ranges(self, start_date, end_date, processing_mode):
        """
        Check if the given date range overlaps with any already processed ranges.
        
        Args:
            start_date (datetime): Start date of the range to check
            end_date (datetime): End date of the range to check
            processing_mode (str): Processing mode ('weekly' or 'monthly')
            
        Returns:
            tuple: (has_overlap: bool, overlapping_ranges: list)
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find overlapping ranges
            cursor.execute('''
                SELECT start_date, end_date, processed_at
                FROM processed_date_ranges
                WHERE processing_mode = ?
                AND (
                    (start_date <= ? AND end_date >= ?) OR  -- New range contains existing range
                    (start_date >= ? AND end_date <= ?) OR  -- Existing range contains new range
                    (start_date <= ? AND end_date >= ?) OR  -- New range overlaps start of existing range
                    (start_date <= ? AND end_date >= ?)     -- New range overlaps end of existing range
                )
            ''', (
                processing_mode,
                start_date.isoformat(), end_date.isoformat(),  # New contains existing
                start_date.isoformat(), end_date.isoformat(),  # Existing contains new
                start_date.isoformat(), start_date.isoformat(),  # New overlaps start of existing
                end_date.isoformat(), end_date.isoformat()       # New overlaps end of existing
            ))
            
            overlapping_ranges = cursor.fetchall()
            conn.close()
            
            has_overlap = len(overlapping_ranges) > 0
            return has_overlap, overlapping_ranges
    
    def cleanup_old_records(self, days_to_keep=90):
        """
        Clean up old processed date records to keep the database size manageable.
        
        Args:
            days_to_keep (int): Number of days to keep records for
            
        Returns:
            int: Number of records removed
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # Clean up old date range records
                cursor.execute('''
                    DELETE FROM processed_date_ranges
                    WHERE processed_at < ?
                ''', (cutoff_date.isoformat(),))
                
                ranges_removed = cursor.rowcount
                
                # Clean up old individual date records
                cursor.execute('''
                    DELETE FROM processed_dates
                    WHERE processed_at < ?
                ''', (cutoff_date.isoformat(),))
                
                dates_removed = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                # Silently clean up old records
                pass
                return ranges_removed + dates_removed
                
            except Exception as e:
                # Silently handle cleanup failure
                pass
                return 0

class DateProcessingLogger:
    """
    Enhanced logger for tracking date processing activities.
    
    This class provides detailed logging for date processing activities, including
    start, completion, and skip notifications with timestamps and performance metrics.
    """
    
    def __init__(self, log_file="date_processing.log"):
        """Initialize the date processing logger"""
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """Set up a dedicated logger for date processing"""
        self.logger = logging.getLogger(f"{__name__}.date_processing")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_processing_start(self, start_date, end_date, processing_mode, additional_info=""):
        """Log the start of date range processing"""
        message = f"START processing date range: {start_date.date()} to {end_date.date()} ({processing_mode} mode)"
        if additional_info:
            message += f" - {additional_info}"
        self.logger.info(message)
        print(f"[DATE PROCESSING] {message}")
    
    def log_processing_complete(self, start_date, end_date, processing_mode, articles_count, duration, additional_info=""):
        """Log the completion of date range processing"""
        message = f"COMPLETE processing date range: {start_date.date()} to {end_date.date()} ({processing_mode} mode)"
        message += f" - Articles: {articles_count}, Duration: {duration}"
        if additional_info:
            message += f" - {additional_info}"
        self.logger.info(message)
        print(f"[DATE PROCESSING] {message}")
    
    def log_processing_skip(self, start_date, end_date, processing_mode, reason, additional_info=""):
        """Log when a date range is skipped"""
        message = f"SKIP processing date range: {start_date.date()} to {end_date.date()} ({processing_mode} mode)"
        message += f" - Reason: {reason}"
        if additional_info:
            message += f" - {additional_info}"
        self.logger.info(message)
        print(f"[DATE PROCESSING] {message}")
    
    def log_overlap_detected(self, start_date, end_date, processing_mode, overlapping_ranges):
        """Log when date overlap is detected"""
        message = f"OVERLAP detected for date range: {start_date.date()} to {end_date.date()} ({processing_mode} mode)"
        message += f" - Overlapping with {len(overlapping_ranges)} ranges:"
        for overlap_start, overlap_end, processed_at in overlapping_ranges:
            message += f" [{overlap_start} to {overlap_end} (processed: {processed_at})]"
        self.logger.warning(message)
        print(f"[DATE PROCESSING] {message}")
    
    def log_database_operation(self, operation, date_range, processing_mode, success, error_message=""):
        """Log database operations for processed dates"""
        status = "SUCCESS" if success else "FAILED"
        message = f"DB {operation} for date range: {date_range[0].date()} to {date_range[1].date()} ({processing_mode} mode) - {status}"
        if error_message:
            message += f" - Error: {error_message}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
        print(f"[DATE PROCESSING] {message}")
    
    def log_summary(self, total_processed, total_skipped, total_overlaps, processing_mode, duration):
        """Log a summary of date processing activities"""
        message = f"SUMMARY - {processing_mode} mode processing completed"
        message += f" - Processed: {total_processed}, Skipped: {total_skipped}, Overlaps: {total_overlaps}"
        message += f" - Total duration: {duration}"
        self.logger.info(message)
        print(f"[DATE PROCESSING] {message}")
    
    def get_processing_statistics(self, processing_mode=None, hours_back=24):
        """Get processing statistics from the log file"""
        try:
            stats = {
                'total_processed': 0,
                'total_skipped': 0,
                'total_overlaps': 0,
                'recent_activity': []
            }
            
            # This is a simple implementation - in production, you might want to parse the log file
            # or use a more sophisticated tracking mechanism
            return stats
        except Exception as e:
            # Silently handle statistics retrieval failure
            pass
            return {}

# Sugar asset configuration
SUGAR_CONFIG = {
    'keywords_main': [
        "sugar", "sugarcane", "sugar beet", "whites", "NY11", "LSU", "LON No. 5", "sugar price", "sugar futures", "Sugar No. 11", "SB", "Sugar No. 5", "Sugar No. 16",
        "Sugar M", "ZCE:SR", "Sugar #11", "SB", "Sugar #5", "Sugar #16"

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
    # Exclusion keywords removed - now only filtering based on sugar-related keywords
    # If an article or its title does not contain sugar-related keywords, it will be excluded
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

# Predefined list of 27 sugar sources with their MEDIA_IDs
# Only articles from these sources with matching MEDIA_ID will be processed
SUGAR_SOURCES_27 = [
    {'name': 'Food Processing', 'id': 171463},
    {'name': 'Sugar Producer', 'id': 124631},
    {'name': 'Argus Media', 'id': 82120},
    {'name': 'Fastmarkets', 'id': 30542},
    {'name': 'Ag Update', 'id': 335679},
    {'name': 'Agriinsite', 'id': 449222},
    {'name': 'Agronews', 'id': 256958},
    {'name': 'Tridge', 'id': 448815},
    {'name': 'ICE', 'id': 999},
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
    {'name': 'CME Group', 'id': 2737765},
    {'name': 'USDA', 'id': 15086},
    {'name': 'FAO', 'id': 53626}
]

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

# Use only the 27 predefined sugar sources
ALL_SUGAR_SOURCES_27 = SUGAR_SOURCES_27
ALL_SUGAR_SOURCE_NAMES_27 = [source['name'] for source in SUGAR_SOURCES_27]

# CRITICAL FIX: Consolidate MEDIA_TOPIC_IDS to reduce duplicate processing
# These topic IDs represent agricultural/commodity topics that should capture sugar-related content
# Using fewer, more relevant topic IDs reduces duplicate articles across different topics
MEDIA_TOPIC_IDS = ['20000386', '20000324', '20000210','20000377','20000361']  # Focus on core agricultural commodity topics

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
    'Benzinga': 0.7,
    'Yahoo! Finance': 0.7,
    'Business Insider': 0.7,
    'Investing': 0.6,
    'CNBC': 0.7,
    'Investing.com Brasil': 0.65,
    'Nasdaq': 0.7,
    'Barchart': 0.6,
    'Market Screener': 0.6,
    'Barron\'s': 0.75,
    'Trading Economics': 0.7,
    'Chini Mandi': 0.8,
    'Globy': 0.8,
    'CME Group': 0.85,
    
    # Government and International Organizations
    'USDA': 0.95,
    'FAO': 0.9
}

def calculate_source_quotas(max_articles, sources_config):
    """
    Calculate dynamic quota allocation for each of the 27 predefined sugar sources based on category weights and reliability scores.
    
    Simplified to work exclusively with the 27 predefined sugar sources.
    
    Args:
        max_articles (int): Maximum total articles to fetch
        sources_config (dict): Configuration of sources organized by category (not used, we use SUGAR_SOURCES_27)
        
    Returns:
        dict: Dictionary mapping source names to their allocated quotas
    """
    # Calculate weighted scores for each of the 27 predefined sugar sources
    source_scores = {}
    total_weight = 0
    
    for source in SUGAR_SOURCES_27:
        source_name = source['name']
        
        # Get category for this source
        category = get_source_category(source_name, SUGAR_SOURCES)
        category_weight = SOURCE_CATEGORY_WEIGHTS.get(category, 0.5)  # Default weight for unknown categories
        
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
    
    # CRITICAL FIX: Ensure we use the full max_articles allocation
    # If we've allocated less than max_articles, distribute remaining articles
    if allocated_articles < max_articles:
        remaining_articles = max_articles - allocated_articles
        
        # Distribute remaining articles to highest reliability sources first
        sorted_sources = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
        
        for source_name, score in sorted_sources:
            if remaining_articles <= 0:
                break
            source_quotas[source_name] += 1
            remaining_articles -= 1
    
    # If we've allocated more than max_articles, scale down proportionally
    elif allocated_articles > max_articles:
        scale_factor = max_articles / allocated_articles
        for source_name in source_quotas:
            source_quotas[source_name] = max(1, int(source_quotas[source_name] * scale_factor))
    
    # Log quota allocation details
    total_allocated = sum(source_quotas.values())
    # Silently log quota allocation
    pass
    
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
    # CRITICAL FIX: Enhanced normalization to ensure consistency across similar content
    import re
    
    def normalize_content(content):
        if not content:
            return ""
        
        # CRITICAL FIX: Preserve multilingual sugar keywords before any processing
        # Create a pattern to match all multilingual sugar keywords
        multilingual_sugar_keywords = [
            # European languages
            "sucre", "azúcar", "zucchero", "açúcar", "zucker", "sukker", "soker", "cukor",
            "cukier", "cukr", "sahara", "ζάχαρη", "cukor", "soker", "sugar", "sukker",
            # Asian languages
            "शक्कर", "चीनी", "চিনি", "சர்க்கரை", "చక్కరో", "ಸಕ್ಕರೆ", "പഞ്ചശര", "සීනි",
            "شکر", "سكر", "शक्कर", "चीनी", "gula", "gularen", "gula aren", "gula merah",
            "น้ำตาล", "น้ำตาลทราย", "อ้อย", "ตะกั่ว", "茶糖", "砂糖", "糖", "설탕", "설탕물",
            # Other major languages
            "şeker", "şekerli", "cukier", "cukrowy", "сахар", "сахарный", "цукор", "цукровий",
            "mishukozi", "asali", "sukari", "chini", "tumbura", "sukali", "sukari", "shakar",
            "shakkar", "misri", "khanda", "gud", "jaggery", "panela", "piloncillo", "rapadura"
        ]
        
        # CRITICAL FIX: Handle German compound words by using a simpler, more direct approach
        # We need to match both exact keywords and keywords that are part of compound words
        # This handles cases like "Zuckerpreis" where "Zucker" is part of the compound word
        
        # First, let's handle German compound words with a special approach
        # We'll look for German sugar keywords within compound words and extract them
        german_compound_keywords = ["zucker", "zuckerrübe", "zuckersirup"]
        
        # Create a map to store all the matches and their placeholders
        keyword_map = {}
        placeholder_count = 0
        
        # Process German compound words first
        for keyword in german_compound_keywords:
            # Find all occurrences of the keyword, including within compound words
            # We'll use a case-insensitive search
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = list(pattern.finditer(content))
            
            for match in matches:
                matched_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Check if this is part of a compound word
                is_compound = False
                
                # Check if it's at the beginning of a compound word (followed by uppercase)
                if end_pos < len(content) and content[end_pos].isupper():
                    is_compound = True
                
                # Check if it's in the middle of a compound word (preceded by lowercase)
                if start_pos > 0 and content[start_pos-1].islower():
                    is_compound = True
                
                # For compound words, we want to preserve the entire compound word
                if is_compound:
                    # Extract the full compound word
                    word_start = start_pos
                    word_end = end_pos
                    
                    # Extend to the beginning of the word
                    while word_start > 0 and content[word_start-1].isalpha():
                        word_start -= 1
                    
                    # Extend to the end of the word
                    while word_end < len(content) and content[word_end].isalpha():
                        word_end += 1
                    
                    compound_word = content[word_start:word_end]
                    placeholder = f"__GERMAN_COMPOUND_SUGAR_{placeholder_count}__"
                    keyword_map[placeholder] = compound_word
                    content = content.replace(compound_word, placeholder)
                    placeholder_count += 1
                else:
                    # For standalone keywords, use the original approach
                    placeholder = f"__STANDALONE_SUGAR_{placeholder_count}__"
                    keyword_map[placeholder] = matched_text
                    content = content.replace(matched_text, placeholder, 1)  # Replace only this occurrence
                    placeholder_count += 1
        
        # Now handle other multilingual keywords with the original approach
        other_keywords = [k for k in multilingual_sugar_keywords if k not in german_compound_keywords]
        if other_keywords:
            other_pattern = '\\b(' + '|'.join(re.escape(keyword) for keyword in other_keywords) + ')\\b'
            other_matches = list(re.finditer(other_pattern, content, re.IGNORECASE))
            
            for match in other_matches:
                matched_text = match.group(0)
                placeholder = f"__OTHER_SUGAR_{placeholder_count}__"
                keyword_map[placeholder] = matched_text
                content = content.replace(matched_text, placeholder, 1)  # Replace only this occurrence
                placeholder_count += 1
        
        # Convert to lowercase
        content = content.lower()
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove URLs, email addresses, and other non-content elements
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        content = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', content)
        
        # Remove punctuation but preserve word boundaries
        # Use a more inclusive pattern that preserves non-Latin characters
        content = re.sub(r'[^\w\s\u0900-\u097F\u0B80-\u0BFF\u0E00-\u0E7F\uAC00-\uD7AF\u3040-\u309F\u30A0-\u30FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF]', ' ', content)
        
        # Restore multilingual sugar keywords from placeholders
        for placeholder, original_text in keyword_map.items():
            # For German compound words, we want to preserve the original case and extract the keyword
            if placeholder.startswith('__GERMAN_COMPOUND_SUGAR_'):
                # Extract the German keyword from the compound word
                for keyword in german_compound_keywords:
                    if keyword.lower() in original_text.lower():
                        # Add the extracted keyword in lowercase
                        content = content.replace(placeholder.lower(), keyword.lower())
                        break
                else:
                    # If no keyword found, just use the original text in lowercase
                    content = content.replace(placeholder.lower(), original_text.lower())
            elif placeholder.startswith('__STANDALONE_SUGAR_'):
                # For standalone keywords, use the original text in lowercase
                content = content.replace(placeholder.lower(), original_text.lower())
            elif placeholder.startswith('__OTHER_SUGAR_'):
                # For other keywords, use the original text in lowercase
                content = content.replace(placeholder.lower(), original_text.lower())
            else:
                # For other keywords, use the original text in lowercase
                content = content.replace(placeholder.lower(), original_text.lower())
        
        # Convert to lowercase
        content = content.lower()
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove URLs, email addresses, and other non-content elements
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        content = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', content)
        
        # Remove punctuation but preserve word boundaries
        # Use a more inclusive pattern that preserves non-Latin characters
        content = re.sub(r'[^\w\s\u0900-\u097F\u0B80-\u0BFF\u0E00-\u0E7F\uAC00-\uD7AF\u3040-\u309F\u30A0-\u30FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF]', ' ', content)
        
        # Restore multilingual sugar keywords from placeholders
        for placeholder, original_text in keyword_map.items():
            # For German compound words, we want to preserve the original case and extract the keyword
            if placeholder.startswith('__GERMAN_COMPOUND_SUGAR_'):
                # Extract the German keyword from the compound word
                for keyword in german_compound_keywords:
                    if keyword.lower() in original_text.lower():
                        # Add the extracted keyword in lowercase
                        content = content.replace(placeholder.lower(), keyword.lower())
                        break
                else:
                    # If no keyword found, just use the original text in lowercase
                    content = content.replace(placeholder.lower(), original_text.lower())
            else:
                # For other keywords, use the original text in lowercase
                content = content.replace(placeholder.lower(), original_text.lower())
        
        # Normalize common variations
        # CRITICAL FIX: Preserve important sugar keywords for triage filter
        # Only normalize generic "sugar" references, but preserve specific sugar terms
        # that are important for the triage filter to detect sugar-related content
        content = re.sub(r'\bsugar\b(?!\s*(cane|beet))', 'sugar', content)  # Only normalize standalone "sugar"
        # DO NOT normalize: sugarcane, sugar beet, whites, NY11, LSU, LON No. 5, etc.
        content = re.sub(r'\b(price|prices|pricing|cost|costs)\b', 'price', content)  # Normalize price terms
        content = re.sub(r'\b(rise|rise|rising|increase|increased|up|higher)\b', 'rise', content)  # Normalize upward movement
        content = re.sub(r'\b(fall|fell|falling|decrease|decreased|down|lower)\b', 'fall', content)  # Normalize downward movement
        content = re.sub(r'\b(market|markets)\b', 'market', content)  # Normalize market terms
        content = re.sub(r'\b(supply|supplies)\b', 'supply', content)  # Normalize supply terms
        content = re.sub(r'\b(demand|demands)\b', 'demand', content)  # Normalize demand terms
        
        # Remove common stop words that don't affect meaning
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        words = content.split()
        words = [word for word in words if word not in stop_words]
        content = ' '.join(words)
        
        # Strip leading/trailing whitespace
        content = content.strip()
        
        return content
    
    normalized_title = normalize_content(title)
    normalized_text = normalize_content(text)
    normalized_source = normalize_content(source)
    
    # Combine normalized content with separators
    content = f"{normalized_title}|{normalized_text}|{normalized_source}"
    
    # Generate hash
    return hashlib.md5(content.encode()).hexdigest()

def is_similar_content(title1, text1, source1, title2, text2, source2, threshold=0.85):
    """
    Check if two articles have similar content using fuzzy matching.
    Returns True if articles are similar, False otherwise.
    
    Args:
        title1, text1, source1: First article's title, text, and source
        title2, text2, source2: Second article's title, text, and source
        threshold: Similarity threshold (0.0 to 1.0) - lowered from 0.9 to 0.85 for better detection
    
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

def count_tokens(text, encoding_name="cl100k_base"):
    """
    Count the number of tokens in a text string using tiktoken.
    
    Args:
        text (str): The text to count tokens for
        encoding_name (str): The encoding name to use (default: cl100k_base for GPT-4)
        
    Returns:
        int: Number of tokens in the text
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        # Silently handle token counting failure
        pass
        # Fallback to rough estimate (1 token ≈ 4 characters for English text)
        return len(text) // 4

def split_article_intelligently(text, max_tokens=1024, min_tokens=512):
    """
    Split article text into parts of max_tokens each, preserving sentence boundaries.
    
    Args:
        text (str): The article text to split
        max_tokens (int): Maximum tokens per part (default: 1024)
        min_tokens (int): Minimum tokens per part (default: 512)
        
    Returns:
        list: List of text parts
    """
    if count_tokens(text) <= max_tokens:
        return [text]
    
    # Silently split article
    pass
    
    # Split by sentences first
    import re
    sentence_endings = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_endings, text)
    
    parts = []
    current_part = ""
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        
        # If adding this sentence would exceed max_tokens and current_part is not empty,
        # finalize the current part and start a new one
        if current_tokens + sentence_tokens > max_tokens and current_part:
            # Only finalize if we have at least min_tokens
            if current_tokens >= min_tokens:
                parts.append(current_part.strip())
                current_part = sentence
                current_tokens = sentence_tokens
            else:
                # If we don't have min_tokens yet, keep adding
                current_part += " " + sentence
                current_tokens += sentence_tokens
        else:
            # Add sentence to current part
            if current_part:
                current_part += " " + sentence
            else:
                current_part = sentence
            current_tokens += sentence_tokens
    
    # Add the last part if it's not empty
    if current_part and current_tokens >= min_tokens:
        parts.append(current_part.strip())
    elif current_part and parts:
        # If the last part is too small, append it to the previous part
        parts[-1] = parts[-1] + " " + current_part
    
    # If we only have one part and it's still too long, split by paragraphs
    if len(parts) == 1 and count_tokens(parts[0]) > max_tokens:
        # Silently try paragraph-based splitting
        pass
        return split_article_by_paragraphs(text, max_tokens, min_tokens)
    
    # Silently complete article splitting
    pass
    return parts

def split_article_by_paragraphs(text, max_tokens=1024, min_tokens=512):
    """
    Split article text by paragraphs as a fallback method.
    
    Args:
        text (str): The article text to split
        max_tokens (int): Maximum tokens per part
        min_tokens (int): Minimum tokens per part
        
    Returns:
        list: List of text parts
    """
    paragraphs = text.split('\n\n')
    parts = []
    current_part = ""
    current_tokens = 0
    
    for paragraph in paragraphs:
        paragraph_tokens = count_tokens(paragraph)
        
        if current_tokens + paragraph_tokens > max_tokens and current_part:
            if current_tokens >= min_tokens:
                parts.append(current_part.strip())
                current_part = paragraph
                current_tokens = paragraph_tokens
            else:
                current_part += "\n\n" + paragraph
                current_tokens += paragraph_tokens
        else:
            if current_part:
                current_part += "\n\n" + paragraph
            else:
                current_part = paragraph
            current_tokens += paragraph_tokens
    
    if current_part:
        parts.append(current_part.strip())
    
    # If we still have a part that's too long, split by word count
    if any(count_tokens(part) > max_tokens for part in parts):
        # Silently try word-based splitting
        pass
        return split_article_by_words(text, max_tokens, min_tokens)
    
    return parts

def split_article_by_words(text, max_tokens=1024, min_tokens=512):
    """
    Split article text by words as a last resort.
    
    Args:
        text (str): The article text to split
        max_tokens (int): Maximum tokens per part
        min_tokens (int): Minimum tokens per part
        
    Returns:
        list: List of text parts
    """
    words = text.split()
    parts = []
    current_part = []
    current_tokens = 0
    
    for word in words:
        word_tokens = count_tokens(word)
        
        if current_tokens + word_tokens > max_tokens and current_part:
            if current_tokens >= min_tokens:
                parts.append(' '.join(current_part))
                current_part = [word]
                current_tokens = word_tokens
            else:
                current_part.append(word)
                current_tokens += word_tokens
        else:
            current_part.append(word)
            current_tokens += word_tokens
    
    if current_part:
        parts.append(' '.join(current_part))
    
    return parts

def normalize_and_filter_article(article, normalization_pipeline):
    """
    Normalize and filter a single article using simplified triage logic.
    Returns structured result dict with asset information or None if not passed.
    
    Enhanced to handle long articles by splitting them into parts when they exceed token limits.
    
    Simplified approach:
    1. Uses only sugar-related keywords for filtering (exclusion keywords removed).
    2. Context zones, structured pricing, and name-entity recognition are only used for metadata extraction.
    3. These features are not used as part of the filtering logic.
    4. Articles are classified as 'Sugar' if they contain sugar-related keywords, 'General' otherwise.
    5. Long articles are split into parts and each part is processed through the triage filter.
    6. If ANY part passes the sugar-related filter, the ENTIRE original article is retained.
    """
    # Combine title and text for normalization
    raw_text = f"{article.get('title', '')}\n{article.get('text', '')}"
    
    # Check if article needs to be split due to token limits
    article_tokens = count_tokens(raw_text)
    max_tokens_per_part = 1024
    
    if article_tokens > max_tokens_per_part:
        # Silently split article due to token limit
        pass
        return process_split_article(article, normalization_pipeline, raw_text, max_tokens_per_part)
    else:
        # Process as a single article (original logic)
        return process_single_article(article, normalization_pipeline, raw_text)

def process_single_article(article, normalization_pipeline, raw_text):
    """
    Process a single article that doesn't need splitting.
    """
    # Normalize the text
    normalized_text = normalization_pipeline.normalize(raw_text)

    # Clean HTML after normalization
    clean_text = clean_html(normalized_text)
    clean_title = clean_html(article.get('title', ''))

    # Apply simplified triage filter (only sugar-related keywords, no exclusion keywords)
    triage_result = triage_filter(clean_text, clean_title)

    # Determine asset based on triage filter result
    triage_passed = triage_result.get("passed", False)
    if triage_passed:
        asset = "Sugar"
    else:
        asset = "General"
    
    # DEBUG: Log asset assignment details
    # Silently assign asset
    pass
    if not triage_passed:
        # Silently handle article triage failure
        pass

    # Extract metadata features (only for enrichment, not for filtering)
    # Context zones metadata
    context_zones_metadata = triage_result.get("matched_zones", [])
    
    # Structured pricing metadata (only for enrichment)
    pricing_structured = []
    if triage_result.get("extracted_sugar_pricing"):
        pricing_structured = normalization_pipeline.normalize(
            sugar_pricing_lines=triage_result["extracted_sugar_pricing"]
        )
    
    # Name-entity recognition metadata (only for enrichment)
    entity_metadata = {
        "matched_keywords": triage_result.get("matched_keywords", []),
        "company_entities": triage_result.get("company_entities", []),
        "government_entities": triage_result.get("government_entities", []),
        "person_entities": triage_result.get("person_entities", [])
    }

    # Compose structured result with metadata features
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
        # Metadata features (not used for filtering)
        "context_zones_metadata": context_zones_metadata,
        "structured_pricing_metadata": pricing_structured,
        "entity_metadata": entity_metadata,
        "raw_article": article,
        "asset": asset,
        "triage_passed": triage_result.get("passed", False),
        "triage_reason": triage_result.get("reason", ""),
        "article_split": False,
        "split_parts": 1,
        "parts_passed": 1 if triage_passed else 0
    }
    return result

def process_split_article(article, normalization_pipeline, raw_text, max_tokens_per_part=1024):
    """
    Process a long article by splitting it into parts and applying the triage filter to each part.
    If ANY part passes the sugar-related filter, the ENTIRE original article is retained.
    """
    # Split the article into parts
    title = article.get('title', '')
    text = article.get('text', '')
    
    # Split the text content (excluding title)
    text_parts = split_article_intelligently(text, max_tokens_per_part)
    
    # Silently process split article
    pass
    
    # Process each part through the triage filter
    all_parts_passed = []
    all_triage_results = []
    any_part_passed = False
    
    for i, part_text in enumerate(text_parts):
        # Silently process article part
        pass
        
        # Combine title with this part for processing
        part_raw_text = f"{title}\n{part_text}"
        
        # Normalize this part
        normalized_part = normalization_pipeline.normalize(part_raw_text)
        clean_part = clean_html(normalized_part)
        clean_title = clean_html(title)
        
        # Apply triage filter to this part with part information
        part_triage_result = triage_filter(clean_part, clean_title, is_part=True, part_number=i+1)
        part_passed = part_triage_result.get("passed", False)
        
        all_parts_passed.append(part_passed)
        all_triage_results.append(part_triage_result)
        
        if part_passed:
            any_part_passed = True
            # Silently handle part passing filter
            pass
        else:
            # Silently handle part failing filter
            pass
    
    # Determine asset based on whether ANY part passed
    if any_part_passed:
        asset = "Sugar"
        # Silently accept article
        pass
    else:
        asset = "General"
        # Silently classify article as General
        pass
    
    # Now process the ENTIRE original article for metadata extraction (not filtering)
    # This ensures we get complete metadata from the full article
    normalized_full_text = normalization_pipeline.normalize(raw_text)
    clean_full_text = clean_html(normalized_full_text)
    clean_title = clean_html(title)
    
    # Apply triage filter to the full article for metadata extraction only
    full_triage_result = triage_filter(clean_full_text, clean_title)
    
    # Extract metadata features from the FULL article (only for enrichment, not for filtering)
    context_zones_metadata = full_triage_result.get("matched_zones", [])
    
    # Structured pricing metadata (only for enrichment)
    pricing_structured = []
    if full_triage_result.get("extracted_sugar_pricing"):
        pricing_structured = normalization_pipeline.normalize(
            sugar_pricing_lines=full_triage_result["extracted_sugar_pricing"]
        )
    
    # Name-entity recognition metadata (only for enrichment)
    entity_metadata = {
        "matched_keywords": full_triage_result.get("matched_keywords", []),
        "company_entities": full_triage_result.get("company_entities", []),
        "government_entities": full_triage_result.get("government_entities", []),
        "person_entities": full_triage_result.get("person_entities", [])
    }

    # Compose structured result with metadata features from the FULL article
    result = {
        "id": generate_article_id(
            article.get('url', ''),
            clean_title,
            article.get('published_date', ''),
            asset
        ),
        "site_name": article.get('site_name', ''),
        "clean_title": clean_title,
        "clean_text": clean_full_text,  # Use the full cleaned text
        "published_date": article.get('published_date', ''),
        "url": article.get('url', ''),
        "score": article.get('score', None),
        # Metadata features from the FULL article (not used for filtering)
        "context_zones_metadata": context_zones_metadata,
        "structured_pricing_metadata": pricing_structured,
        "entity_metadata": entity_metadata,
        "raw_article": article,
        "asset": asset,
        "triage_passed": any_part_passed,  # Based on whether ANY part passed
        "triage_reason": "Passed sugar keyword filter (split article)" if any_part_passed else "No sugar-related keywords found in any part",
        "article_split": True,
        "split_parts": len(text_parts),
        "parts_passed": sum(1 for passed in all_parts_passed if passed),
        "part_results": all_triage_results  # Store individual part results for debugging
    }
    return result

def fetch_sugar_articles_for_period(api_key, start_date, end_date, topic_ids, max_articles=30000, normalization_pipeline=None, global_dedup_cache=None):
    """
    Fetch and process sugar news articles for a given period and topic IDs.
    Returns a DataFrame of structured, filtered articles.
    
    CRITICAL: Implements DOUBLE FILTERING by both MEDIA_ID and MEDIA_TOPIC_ID:
    1. Articles must be from one of the 27 predefined sugar sources (matching MEDIA_ID)
    2. Articles must have one of the predefined MEDIA_TOPIC_IDs
    3. Only articles that pass BOTH filters are processed further
    
    ENHANCED: Double filtering is now implemented at the API level for maximum efficiency:
    - MEDIA_ID filtering: Uses site_id parameter in API calls
    - MEDIA_TOPIC_ID filtering: Uses media_topic_ids parameter in API calls
    - Additional validation is performed on returned results to ensure double filtering worked correctly
    
    CRITICAL FIX: Enhanced deduplication to prevent processing same articles across different topic IDs:
    - Global deduplication cache now persists across all topic ID processing calls
    - Content hash generation includes source information for better accuracy
    - Similarity checking prevents near-duplicates from different sources
    
    Simplified to exclusively fetch from 27 predefined sugar sources with matching MEDIA_IDs.
    All quota allocated to the 27 predefined sugar sources only.
    Uses simplified triage filter focused on sugar-related keywords only.
    Context zones, structured pricing, and name-entity recognition are used only for metadata extraction.
    
    Args:
        api_key: Opoint API key
        start_date: Start date for fetching articles
        end_date: End date for fetching articles
        topic_ids: List of topic IDs to search (MEDIA_TOPIC_IDs)
        max_articles: Maximum number of articles to fetch
        normalization_pipeline: Language normalization pipeline
        global_dedup_cache: Global cache for cross-topic deduplication (optional)
    """
    global request_counter
    with request_lock:
        request_counter += 1
        current_request_id = request_counter
    
    # Silently start fetch
    pass
    
    # CRITICAL FIX: Initialize global deduplication cache if not provided with enhanced structure
    if global_dedup_cache is None:
        global_dedup_cache = {
            'seen_content_hashes': set(),
            'seen_article_ids': set(),
            'seen_urls': set(),  # CRITICAL: Track URLs to prevent duplicates
            'processed_articles': [],
            'cache_stats': {
                'total_hashes_added': 0,
                'total_duplicates_prevented': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'similarity_checks': 0,
                'similarity_duplicates': 0,
                'url_duplicates': 0  # Track URL-based duplicates
            },
            'processing_date': start_date.date()  # Track processing date for cache management
        }
        # Silently initialize cache
        pass
    else:
        # Ensure cache has enhanced statistics structure
        if 'cache_stats' not in global_dedup_cache:
            global_dedup_cache['cache_stats'] = {
                'total_hashes_added': 0,
                'total_duplicates_prevented': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'similarity_checks': 0,
                'similarity_duplicates': 0,
                'url_duplicates': 0
            }
        # CRITICAL FIX: Add URL tracking if not present
        if 'seen_urls' not in global_dedup_cache:
            global_dedup_cache['seen_urls'] = set()
        if 'processing_date' not in global_dedup_cache:
            global_dedup_cache['processing_date'] = start_date.date()
            
        # Silently use existing cache
        pass
    
    # Acquire semaphore to limit concurrent API requests
    # Silently acquire semaphore
    pass
    acquired = active_requests.acquire(timeout=60)  # Wait up to 60 seconds for a slot
    if not acquired:
        # Silently handle semaphore timeout
        pass
        raise Exception("Timeout waiting for available API request slot")
    
    try:
        # Silently create API instance
        pass
        api = OpointAPI(api_key=api_key)
        
        # Build search query for the 27 predefined sugar sources
        # Silently build search query
        pass
        sugar_search_query = build_search_query(
            topic_ids,
            SUGAR_CONFIG['person_entities'],
            SUGAR_CONFIG['company_entities'],
            ALL_SUGAR_SOURCE_NAMES_27
        )

        # Silently fetch articles
        pass
        # Silently fetch articles
        pass
        
        # Calculate dynamic quota allocation for the 27 predefined sugar sources - now using ALL quota
        sugar_source_quotas = calculate_source_quotas(max_articles, SUGAR_SOURCES)  # Use ALL of max_articles for the 27 sugar sources
        
        # Log quota allocation
        # Silently allocate quotas
        pass
        total_sugar_quota = 0
        for source, quota in sugar_source_quotas.items():
            category = get_source_category(source, SUGAR_SOURCES)
            reliability = SOURCE_RELIABILITY_SCORES.get(source, 0.5)
            # Silently display quota allocation
            pass
            total_sugar_quota += quota
        # Silently display total quota
        pass
        
        # === STEP 1: Fetch articles from sugar sources ONLY ===
        # Silently start step 1
        pass
        # Silently start step 1
        pass
        
        sugar_results = []
        
        # Process only the 27 predefined sugar sources
        # Silently process sugar sources
        pass
        # Silently process sugar sources
        pass
        
        for source in ALL_SUGAR_SOURCES_27:
            # Get enhanced dynamic quota for this source
            source_quota = sugar_source_quotas.get(source['name'], 10)  # Default to 10 if not found
            
            try:
                # Silently make API call
                pass
                # CRITICAL FIX: Implement DOUBLE FILTERING by both MEDIA_ID and MEDIA_TOPIC_ID
                # Use source ID directly with site_id parameter to ensure only articles with matching MEDIA_ID are processed
                # AND explicitly pass media_topic_ids to ensure only articles with matching MEDIA_TOPIC_ID are returned
                if source['id']:
                    # Ensure site_id is passed as string to match API's expected format
                    site_id_str = str(source['id'])
                    # Silently use site_id
                    pass
                    
                    results = api.search_articles(
                        site_id=site_id_str,
                        search_text=sugar_search_query,
                        num_articles=source_quota,  # Use enhanced quota
                        min_score=0.77,
                        start_date=start_date,
                        end_date=end_date,
                        media_topic_ids=topic_ids,  # CRITICAL: Explicitly pass MEDIA_TOPIC_IDs for double filtering
                        timeout=30  # 30 second timeout
                    )
                else:
                    # Fallback to source name if ID is not available
                    results = api.search_site_and_articles(
                        site_name=None,
                        search_text=sugar_search_query,
                        source=source['name'],
                        num_articles=source_quota,  # Use enhanced quota
                        min_score=0.77,
                        start_date=start_date,
                        end_date=end_date,
                        media_topic_ids=topic_ids,  # CRITICAL: Explicitly pass MEDIA_TOPIC_IDs for double filtering
                        timeout=30  # 30 second timeout
                    )
                
                if not results.empty:
                    # CRITICAL FIX: Validate DOUBLE FILTERING - ensure articles have both correct MEDIA_ID and MEDIA_TOPIC_ID
                    # The API now performs double filtering at the server level, but we validate the results here
                    # First filter: Check if articles have the correct MEDIA_ID (source ID)
                    if 'id_site' in results.columns:
                        # CRITICAL FIX: Handle type mismatch - API returns strings, config has integers
                        # Convert both to strings for comparison
                        expected_id = str(source['id'])
                        media_id_filtered = results[results['id_site'].astype(str) == expected_id].copy()
                        # Silently validate MEDIA_ID
                        pass
                    else:
                        # If id_site column is not available, assume all articles are from the correct source
                        media_id_filtered = results.copy()
                        # Silently handle missing id_site column
                        pass
                    
                    # Second filter: Validate that articles have the correct MEDIA_TOPIC_ID
                    # This is a validation step since the API should have already filtered by MEDIA_TOPIC_ID
                    # But we add additional validation to ensure double filtering worked correctly
                    if 'topics' in results.columns or 'topic_ids' in results.columns:
                        # If topic information is available, validate by MEDIA_TOPIC_ID
                        topic_column = 'topics' if 'topics' in results.columns else 'topic_ids'
                        validated_results = []
                        
                        for _, article in media_id_filtered.iterrows():
                            article_topics = article.get(topic_column, [])
                            if isinstance(article_topics, str):
                                # Try to parse as JSON if it's a string
                                try:
                                    import json
                                    article_topics = json.loads(article_topics)
                                except:
                                    article_topics = []
                            
                            # Check if any of the article's topic IDs match our MEDIA_TOPIC_IDs
                            has_valid_topic = False
                            if isinstance(article_topics, list):
                                for topic in article_topics:
                                    if isinstance(topic, dict) and 'id' in topic:
                                        topic_id = str(topic['id'])
                                        if topic_id in topic_ids:
                                            has_valid_topic = True
                                            break
                                    elif isinstance(topic, str):
                                        if topic in topic_ids:
                                            has_valid_topic = True
                                            break
                            
                            if has_valid_topic:
                                validated_results.append(article)
                        
                        validated_df = pd.DataFrame(validated_results)
                        # Silently validate MEDIA_TOPIC_ID
                        pass
                    else:
                        # If topic information is not available in the results, assume the API filtered correctly
                        validated_df = media_id_filtered.copy()
                        # Silently handle missing topic information
                        pass
                    
                    if not validated_df.empty:
                        sugar_results.append(validated_df)
                        # Silently handle found articles
                        pass
                        # Silently handle found articles
                        pass
                    else:
                        # Silently handle no articles passing filter
                        pass
                        # Silently handle no articles passing filter
                        pass
                else:
                    # Silently handle no articles found
                    pass
                    # Silently handle no articles found
                    pass
            except Exception as e:
                # Silently handle fetch error
                pass
                # Silently handle fetch error
                pass
        
        # Combine sugar results
        if sugar_results:
            all_results = pd.concat(sugar_results, ignore_index=True)
            # Silently handle total articles
            pass
            # Silently handle total articles
            pass
        else:
            all_results = pd.DataFrame()
            logger.info(f"[Request-{current_request_id}] No articles found from sugar sources")
            # Silently handle no articles found
            pass
            return pd.DataFrame()

        # === STEP 2: Apply normalization and triage pipeline to sugar articles only ===
        # Silently start step 2
        pass
        # Silently start step 2
        pass
        
        structured_articles = []
        triage_passed_count = 0
        triage_failed_count = 0
        duplicates_removed_count = 0  # Track actual duplicates removed
        
        # CRITICAL FIX: Enhanced deduplication with global cache and URL tracking
        # First pass: Normalize all articles and generate hashes for better deduplication
        normalized_articles = []
        for _, article in all_results.iterrows():
            # CRITICAL FIX: Check URL-based deduplication first (most reliable)
            article_url = article.get('url', '').strip()
            if article_url and article_url in global_dedup_cache['seen_urls']:
                # Silently handle URL duplicate
                pass
                duplicates_removed_count += 1
                global_dedup_cache['cache_stats']['url_duplicates'] += 1
                global_dedup_cache['cache_stats']['total_duplicates_prevented'] += 1
                continue
            
            # Normalize the article for better deduplication
            result = normalize_and_filter_article(article, normalization_pipeline)
            if result:
                # Generate content hash using normalized content for better accuracy
                title = result.get('clean_title', '')
                text = result.get('clean_text', '')
                source = result.get('site_name', '') or result.get('source_name', '')
                content_hash = generate_content_hash(title, text, source)
                
                # Store normalized article with hash and URL
                normalized_articles.append({
                    'result': result,
                    'content_hash': content_hash,
                    'title': title,
                    'text': text,
                    'source': source,
                    'article_id': result.get('id', ''),
                    'url': article_url  # CRITICAL: Store URL for deduplication
                })
        
        # Second pass: Apply enhanced deduplication with global cache
        max_similarity_check = 5000  # Sliding window size for similarity checking
        
        for article_data in normalized_articles:
            content_hash = article_data['content_hash']
            title = article_data['title']
            text = article_data['text']
            source = article_data['source']
            result = article_data['result']
            article_id = article_data['article_id']
            article_url = article_data['url']
            
            # CRITICAL FIX: Check global deduplication cache first (multiple layers)
            # 1. Check content hash (most reliable for exact duplicates)
            if content_hash in global_dedup_cache['seen_content_hashes']:
                # Silently handle content hash duplicate
                pass
                duplicates_removed_count += 1
                global_dedup_cache['cache_stats']['cache_hits'] += 1
                global_dedup_cache['cache_stats']['total_duplicates_prevented'] += 1
                continue
                
            # 2. Check article ID (backup for content hash)
            if article_id in global_dedup_cache['seen_article_ids']:
                # Silently handle article ID duplicate
                pass
                duplicates_removed_count += 1
                global_dedup_cache['cache_stats']['cache_hits'] += 1
                global_dedup_cache['cache_stats']['total_duplicates_prevented'] += 1
                continue
            
            # 3. Check for similar content with globally processed articles
            is_duplicate = False
            # Use global cache for similarity checking
            recent_articles = global_dedup_cache['processed_articles'][-max_similarity_check:] if len(global_dedup_cache['processed_articles']) > max_similarity_check else global_dedup_cache['processed_articles']
            
            for processed_article in recent_articles:
                global_dedup_cache['cache_stats']['similarity_checks'] += 1
                if is_similar_content(
                    title, text, source,
                    processed_article['title'], processed_article['text'], processed_article['source']
                ):
                    is_duplicate = True
                    # Silently handle similarity duplicate
                    pass
                    duplicates_removed_count += 1
                    global_dedup_cache['cache_stats']['similarity_duplicates'] += 1
                    global_dedup_cache['cache_stats']['total_duplicates_prevented'] += 1
                    break
            
            if is_duplicate:
                continue
            
            # CRITICAL FIX: Add to global deduplication cache (multiple layers)
            global_dedup_cache['seen_content_hashes'].add(content_hash)
            global_dedup_cache['seen_article_ids'].add(article_id)
            if article_url:  # Only add non-empty URLs
                global_dedup_cache['seen_urls'].add(article_url)
            global_dedup_cache['cache_stats']['total_hashes_added'] += 1
            global_dedup_cache['cache_stats']['cache_misses'] += 1
            
            # Store article info for global similarity checking
            global_dedup_cache['processed_articles'].append({
                'title': title,
                'text': text,
                'source': source
            })
            
            # Periodically clean up old articles to prevent memory buildup
            if len(global_dedup_cache['processed_articles']) > max_similarity_check * 2:
                global_dedup_cache['processed_articles'] = global_dedup_cache['processed_articles'][-max_similarity_check:]
                # Silently clean up cache
                pass
            
            # Add the normalized result to structured articles
            result['content_hash'] = content_hash
            structured_articles.append(result)
            
            # Track triage filter results with enhanced logging
            if result.get('triage_passed', False):
                triage_passed_count += 1
                # Silently handle article passing triage
                pass
            else:
                triage_failed_count += 1
                # Silently handle article failing triage
                pass

        if not structured_articles:
            # Silently handle no articles processed
            pass
            # Silently handle no articles processed
            pass
            return pd.DataFrame()

        # Log triage filter statistics
        # Silently display triage filter results
        pass
        
        # Log article splitting statistics
        split_articles = [article for article in structured_articles if article.get('article_split', False)]
        if split_articles:
            # Silently display article splitting statistics
            pass
            
            total_parts = sum(article.get('split_parts', 1) for article in split_articles)
            avg_parts_per_article = total_parts / len(split_articles) if split_articles else 0
            
            # Silently display parts statistics
            pass
            
            # Log split articles that passed the filter
            split_passed = [article for article in split_articles if article.get('triage_passed', False)]
            if split_passed:
                # Silently display split articles that passed
                pass
                
                # Show details of split articles that passed
                for article in split_passed[:5]:  # Show first 5
                    title = article.get('clean_title', 'No title')[:80]
                    parts = article.get('split_parts', 1)
                    passed_parts = article.get('parts_passed', 0)
                    # Silently display split article details
                    pass
                
                if len(split_passed) > 5:
                    # Silently display remaining split articles
                    pass
            else:
                # Silently handle no split articles passing
                pass

        # Report ACTUAL deduplication statistics
        original_count = len(all_results)
        after_deduplication_count = len(structured_articles)
        # Silently display deduplication statistics
        pass
        if duplicates_removed_count > 0:
            # Silently display deduplication details
            pass
            
            # Report detailed cache statistics
            cache_stats = global_dedup_cache.get('cache_stats', {})
            if cache_stats:
                # Silently display cache performance statistics
                pass
                
                # Calculate cache hit rate
                total_cache_operations = cache_stats.get('cache_hits', 0) + cache_stats.get('cache_misses', 0)
                if total_cache_operations > 0:
                    hit_rate = (cache_stats.get('cache_hits', 0) / total_cache_operations) * 100
                    # Silently display cache hit rate
                    pass
                
                # Calculate similarity detection rate
                similarity_checks = cache_stats.get('similarity_checks', 0)
                if similarity_checks > 0:
                    similarity_detection_rate = (cache_stats.get('similarity_duplicates', 0) / similarity_checks) * 100
                    # Silently display similarity detection rate
                    pass
        else:
            # Silently handle no duplicates
            pass

        # Convert to DataFrame
        df_structured = pd.DataFrame(structured_articles)

        # Apply source filtering to sugar articles only
        # Silently start step 3
        pass
        # Silently start step 3
        pass
        df_structured = filter_trusted_sources(df_structured, verbose=True)

        # Report source filtering statistics (separate from deduplication)
        after_source_filtering_count = len(df_structured)
        source_filtered_count = after_deduplication_count - after_source_filtering_count
        if source_filtered_count > 0:
            # Silently display source filtering statistics
            pass

        # Log source distribution - only the 27 predefined sugar sources
        if not df_structured.empty:
            sugar_source_articles = df_structured[df_structured['site_name'].isin(ALL_SUGAR_SOURCE_NAMES_27)]
            sugar_source_count = len(sugar_source_articles)
            
            # Silently display source distribution analysis
            pass
            
            # Special logging for the 27 sugar sources
            if sugar_source_count > 0:
                # Silently display sugar sources analysis
                pass
                
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
                    
                    # Silently display source details
                    pass
                
                # Overall sugar source statistics
                total_sugar_passed = len(sugar_source_articles[sugar_source_articles['asset'] == 'Sugar'])
                overall_sugar_pass_rate = (total_sugar_passed / sugar_source_count) * 100 if sugar_source_count > 0 else 0
                
                # Calculate overall quota utilization
                total_allocated_quota = sum(sugar_source_quotas.values())
                overall_quota_utilization = (sugar_source_count / total_allocated_quota * 100) if total_allocated_quota > 0 else 0
                
                # Silently display overall performance
                pass
                
                # Monthly interval analysis
                month_start = start_date.strftime("%Y-%m-%d")
                month_end = end_date.strftime("%Y-%m-%d")
                days_in_month = (end_date - start_date).days + 1
                # Silently display monthly interval analysis
                pass
            
            # Note: Only the 27 predefined sugar sources are processed
            # Silently display source selection summary
            pass

        # Silently complete processing
        pass
        return df_structured
    
    except Exception as e:
        # Silently handle exception
        pass
        raise
    finally:
        # Always release the semaphore
        active_requests.release()
        # Silently release semaphore
        pass

def generate_monthly_date_ranges(months_back=12):
    """Generate list of (start_date, end_date) tuples for the last N months"""
    date_ranges = []
    current_date = datetime.now()
    
    for i in range(months_back):
        # Calculate the target month by subtracting i months from the current date
        # Handle year rollover correctly
        year = current_date.year
        month = current_date.month - i
        
        while month <= 0:
            month += 12
            year -= 1
        
        # Create start of month (first day at midnight)
        start_of_month = datetime(year, month, 1, 0, 0, 0, 0)
        
        # Calculate end of month (last day at 23:59:59)
        if month == 12:
            next_month = datetime(year + 1, 1, 1, 0, 0, 0, 0)
        else:
            next_month = datetime(year, month + 1, 1, 0, 0, 0, 0)
        
        end_of_month = next_month - timedelta(seconds=1)
        
        date_ranges.append((start_of_month, end_of_month))
    
    # Reverse to chronological order (oldest first)
    date_ranges.reverse()
    return date_ranges

def main():
    parser = argparse.ArgumentParser(description="Fetch and filter sugar news articles from 27 predefined sugar sources with simplified filtering")
    parser.add_argument('--dry-run', action='store_true', help='Print what would be done without executing')
    parser.add_argument('--max-workers', type=int, default=2, help='Maximum number of concurrent workers (default: 2)')
    parser.add_argument('--months-back', type=int, default=12, help='Number of months back to fetch (default: 12, approx 1 year)')
    parser.add_argument('--max-articles', type=int, default=5000, help='Maximum articles per request (default: 5000)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint if available')
    parser.add_argument('--checkpoint-dir', type=str, default='./checkpoints', help='Directory for storing checkpoints (default: ./checkpoints)')
    parser.add_argument('--processed-dates-db', type=str, default='processed_dates.db',
                        help='Database file for tracking processed dates (default: processed_dates.db)')
    parser.add_argument('--skip-processed', action='store_true',
                        help='Skip already processed date ranges (default: False)')
    parser.add_argument('--cleanup-old-records', type=int, default=90,
                        help='Clean up processed date records older than N days (default: 90)')
    parser.add_argument('--max-memory-mb', type=int, default=4000,
                        help='Maximum memory usage in MB before triggering cleanup (default: 4000)')
    args = parser.parse_args()

    api_key = os.getenv('OPOINT_API_KEY')
    if not api_key:
        # Silently handle missing API key
        pass
        return

    # Initialize processed dates tracker
    processed_dates_tracker = ProcessedDatesTracker(args.processed_dates_db)
    # Silently initialize tracker
    pass
    
    # Initialize date processing logger
    date_processing_logger = DateProcessingLogger()
    # Silently initialize logger
    pass
    
    # Clean up old records if requested
    if args.cleanup_old_records > 0:
        cleaned_count = processed_dates_tracker.cleanup_old_records(args.cleanup_old_records)
        # Silently clean up old records
        pass

    # Generate monthly date ranges
    date_ranges = generate_monthly_date_ranges(args.months_back)
    period_type = "months"
    period_count = args.months_back
    
    total_tasks = len(date_ranges) * len(MEDIA_TOPIC_IDS)
    # Silently start processing
    pass
    
    # Silently start processing
    pass

    if args.dry_run:
        # Silently handle dry run
        pass
        return

    normalization_pipeline = LanguageNormalizationPipeline()

    start_time = datetime.now()
    total_saved = 0
    all_structured = []

    # Check for resume option and load intermediate results if available
    if args.resume:
        # Silently enable resume mode
        pass
        loaded_results = load_intermediate_results(args.checkpoint_dir)
        if loaded_results:
            all_structured = loaded_results
            total_saved = sum(len(df) for df in all_structured)
            # Silently load results
            pass
            # Silently resume with checkpoints
            pass
        else:
            # Silently start fresh
            pass
            # Silently start fresh
            pass

    # Global exception handler to ensure intermediate results are preserved
    try:
        # Monthly processing
        # Silently start monthly processing
        pass
        # Silently start monthly processing
        pass
        
        completed_months = 0
        failed_months = 0
        total_articles_saved = 0
        
        # Process each month separately
        for month_idx, (start_date, end_date) in enumerate(date_ranges):
            month_name = start_date.strftime("%B %Y")
            
            # Check if this month has already been processed
            if args.skip_processed and processed_dates_tracker.is_date_range_processed(start_date, end_date, 'monthly'):
                # Silently skip processed month
                pass
                date_processing_logger.log_processing_skip(
                    start_date, end_date, 'monthly',
                    "Already processed in database",
                    f"Month: {month_name}"
                )
                # Silently skip processed month
                pass
                continue
            
            # Check for overlaps with processed ranges
            has_overlap, overlapping_ranges = processed_dates_tracker.check_overlap_with_processed_ranges(start_date, end_date, 'monthly')
            if has_overlap:
                # Silently handle overlap
                pass
                date_processing_logger.log_overlap_detected(start_date, end_date, 'monthly', overlapping_ranges)
                # Silently handle overlap
                pass
                
                if args.skip_processed:
                    date_processing_logger.log_processing_skip(
                        start_date, end_date, 'monthly',
                        "Overlap with previously processed ranges",
                        f"Month: {month_name}, Overlaps: {len(overlapping_ranges)}"
                    )
                    # Silently skip month due to overlap
                    pass
                    continue
            
            # Log the start of processing
            date_processing_logger.log_processing_start(
                start_date, end_date, 'monthly',
                f"Month: {month_name}, Index: {month_idx+1}/{len(date_ranges)}"
            )
            
            # Silently process month
            pass
            # Silently process month
            pass
            
            month_start_time = datetime.now()
            month_articles = []
            month_completed_tasks = 0
            month_failed_tasks = 0
            
            # CRITICAL FIX: Initialize enhanced global deduplication cache for this month
            # This prevents duplicate processing across different topic IDs with multiple layers of deduplication
            global_dedup_cache = {
                'seen_content_hashes': set(),
                'seen_article_ids': set(),
                'seen_urls': set(),  # CRITICAL: Track URLs to prevent duplicates
                'processed_articles': [],
                'cache_stats': {
                    'total_hashes_added': 0,
                    'total_duplicates_prevented': 0,
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'similarity_checks': 0,
                    'similarity_duplicates': 0,
                    'url_duplicates': 0  # Track URL-based duplicates
                },
                'processing_date': start_date.date()  # Track processing date for cache management
            }
            
            # Silently initialize cache
            pass
            # Silently initialize cache
            pass
            
            # Process all topic IDs for this month
            for topic_idx, topic_id in enumerate(MEDIA_TOPIC_IDS):
                # Silently process topic
                pass
                
                try:
                    # Check memory usage before processing each topic
                    if not check_memory_usage(max_memory_mb=args.max_memory_mb):
                        # Silently handle high memory usage
                        pass
                        cleanup_memory()
                        time.sleep(2)
                    
                    # Pass global deduplication cache to prevent duplicates across topics
                    df_structured = fetch_sugar_articles_for_period(
                        api_key, start_date, end_date, [topic_id], args.max_articles, normalization_pipeline, global_dedup_cache
                    )
                    
                    if not df_structured.empty:
                        month_articles.append(df_structured)
                        # Silently complete topic
                        pass
                        # Silently display topic results
                        pass
                    else:
                        # Silently handle no results
                        pass
                        # Silently handle no articles found
                        pass
                    
                    month_completed_tasks += 1
                    time.sleep(0.5)  # Delay to prevent overwhelming the system
                    
                except Exception as e:
                    month_failed_tasks += 1
                    # Silently handle topic failure
                    pass
                    # Silently handle topic failure
                    pass
            
            # Process month results
            month_end_time = datetime.now()
            month_duration = month_end_time - month_start_time
            
            if month_articles:
                # Concatenate all articles for this month
                month_df = pd.concat(month_articles, ignore_index=True)
                
                # Log month statistics
                month_total_articles = len(month_df)
                month_sugar_articles = len(month_df[month_df['asset'] == 'Sugar'])
                month_general_articles = len(month_df[month_df['asset'] == 'General'])
                
                print(f"\n=== MONTH {month_name} STATISTICS ===")
                print(f"Total articles processed: {month_total_articles}")
                print(f"Sugar articles (passed triage): {month_sugar_articles}")
                print(f"General articles (failed triage): {month_general_articles}")
                print(f"Processing duration: {month_duration}")
                print(f"Tasks completed: {month_completed_tasks}, Failed: {month_failed_tasks}")
                
                # Save to database for this month
                search_metadata = {
                    'topic_ids': MEDIA_TOPIC_IDS,
                    'keywords_main': SUGAR_CONFIG['keywords_main'],
                    # Exclusion keywords removed - now only filtering based on sugar-related keywords
                    'keywords_context_zones': SUGAR_CONFIG['keywords_context_zones'],
                    'company_entities': SUGAR_CONFIG['company_entities'],
                    'government_entities': SUGAR_CONFIG['government_entities'],
                    'person_entities': SUGAR_CONFIG['person_entities'],
                    'search_period': f"{start_date.date()} to {end_date.date()}",
                    'processing_mode': 'monthly'
                }
                
                # Save only articles that passed the triage filter (asset='Sugar')
                # Silently debug database save
                pass
                
                month_sugar_only_df = month_df[month_df['asset'] == 'Sugar'].copy()
                
                # Silently debug database save
                pass
                
                if not args.dry_run and not month_sugar_only_df.empty:
                    try:
                        month_saved_count = save_to_database(month_sugar_only_df, search_metadata, 'Sugar')
                        total_articles_saved += month_saved_count
                        print(f"Saved {month_saved_count} articles to database for {month_name}")
                        
                        # Log breakdown by asset type for this month
                        print(f"Breakdown for {month_name}:")
                        print(f"  - Sugar articles saved: {month_saved_count}")
                        print(f"  - General articles (not saved): {month_general_articles}")
                        
                    except Exception as e:
                        # Silently handle database save failure
                        pass
                        # Silently handle database save error
                        pass
                elif args.dry_run:
                    # Silently handle dry run
                    pass
                
                # Add to overall results for final summary
                all_structured.append(month_df)
                total_saved += month_total_articles
                
                # Mark this month as processed in the tracker
                if not args.dry_run:
                    mark_success = processed_dates_tracker.mark_date_range_processed(start_date, end_date, 'monthly')
                    if mark_success:
                        # Silently mark month as processed
                        pass
                        date_processing_logger.log_database_operation(
                            "MARK_PROCESSED", (start_date, end_date), 'monthly', True
                        )
                        print(f"Marked month {month_name} as processed in database")
                    else:
                        # Silently handle marking failure
                        pass
                        date_processing_logger.log_database_operation(
                            "MARK_PROCESSED", (start_date, end_date), 'monthly', False,
                            f"Failed to mark month {month_name} as processed"
                        )
                        # Silently handle marking failure
                        pass
                
                # Log completion of processing
                month_end_time = datetime.now()
                month_duration = month_end_time - month_start_time
                date_processing_logger.log_processing_complete(
                    start_date, end_date, 'monthly',
                    month_total_articles, month_duration,
                    f"Month: {month_name}, Saved: {month_saved_count if 'month_saved_count' in locals() else 0}"
                )
                
                completed_months += 1
            else:
                # Silently handle no articles processed
                pass
                failed_months += 1
            
            # MEMORY CLEANUP after each month
            # Silently run memory cleanup
            pass
            # Silently run memory cleanup
            pass
            
            # Clear month-specific data structures
            month_articles.clear()
            if 'month_df' in locals():
                del month_df
            if 'month_sugar_only_df' in locals():
                del month_sugar_only_df
            
            # Force garbage collection
            cleanup_memory()
            
            # Check memory usage after cleanup
            if PSUTIL_AVAILABLE:
                # Silently check memory usage
                pass
            
            # Add delay between months to allow system resources to free up
            if month_idx < len(date_ranges) - 1:  # Not the last month
                # Silently pause before next month
                pass
                time.sleep(15)
            
            # Silently complete month
            pass
        
        # Monthly processing completed
        # Silently complete monthly processing
        pass
        # Silently complete monthly processing
        pass

        # Concatenate all results (for weekly mode or final summary)
        if all_structured:
            final_df = pd.concat(all_structured, ignore_index=True)
            
            # Log overall statistics
            total_articles = len(final_df)
            sugar_articles = len(final_df[final_df['asset'] == 'Sugar'])
            general_articles = len(final_df[final_df['asset'] == 'General'])
            
            # Silently display overall statistics
            pass
            
            # Note: Weekly processing has been removed - only monthly processing is now supported
        else:
            # Silently handle no articles processed
            pass

        end_time = datetime.now()
        duration = end_time - start_time
        # Silently complete sugar news fetch
        pass
        
        # Silently display processed intervals
        pass
        
        # Calculate and display monthly statistics
        if len(date_ranges) > 0:
            total_months = len(date_ranges)
            avg_articles_per_month = total_saved / total_months if total_months > 0 else 0
            # Silently display average articles
            pass
            
            # Calculate date span in months
            date_span_months = (date_ranges[0][1] - date_ranges[-1][0]).days / 30.44  # Average days per month
            # Silently display date span
            pass
        # Display dynamic quota allocation summary (common for both modes)
        # Silently display quota allocation summary
        pass
        
        # Silently display top sources
        pass
        for source, reliability in top_sources:
            category = get_source_category(source, SUGAR_SOURCES)
            # Silently display source reliability
            pass
            
        # Silently display pipeline modification summary
        pass
    
    except Exception as e:
        # Silently handle fatal error
        pass
        # Silently handle fatal error
        pass
        return 1
    
    finally:
        # This block always executes, whether there was an exception or not
        end_time = datetime.now()
        duration = end_time - start_time
        # Silently end process
        pass
        
        # Log processing summary
        if 'date_processing_logger' in locals():
            total_processed = completed_months
            total_skipped = 0  # This would need to be tracked during processing
            total_overlaps = 0  # This would need to be tracked during processing
            date_processing_logger.log_summary(
                total_processed, total_skipped, total_overlaps,
                'monthly', duration
            )
        
        # If we're exiting with an error or interruption, ensure intermediate results are preserved
        if 'failed_tasks' in locals() and failed_tasks > 0:
            # Silently handle failed tasks
            pass
            # Silently handle failed tasks
            pass

if __name__ == "__main__":
    main()
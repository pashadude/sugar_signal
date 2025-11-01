#!/usr/bin/env python
"""
Enhanced highly optimized parallel sentiment prediction for sugar articles.
Processes sugar articles with maximum parallelization using multiple API keys.
"""
import os
import sys
import json
import time
import hashlib
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from clickhouse_driver import Client
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import threading
import queue
import multiprocessing as mp
from typing import List, Optional, Dict, Any

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # Go up to sugar examples root
sys.path.insert(0, str(parent_dir))

# Import the required modules
try:
    from backend.api.nebius.nebius_api import NebiusAPI
    from backend.config import CLICKHOUSE_NATIVE_CONFIG
    print("Successfully imported using relative path")
except ImportError as e:
    print(f"Import attempt failed: {e}")
    # If still not found, we'll handle it in the main function
    NebiusAPI = None
    CLICKHOUSE_NATIVE_CONFIG = None
    print("Import failed, setting modules to None")

# Sugar commodity to process
SUGAR_COMMODITY = ['Sugar']

# Global counters and locks
processed_articles = 0
total_articles = 0
successful_predictions = 0
failed_predictions = 0
api_key_usage = {}
lock = threading.Lock()
api_lock = threading.Lock()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sugar_sentiment_prediction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_progress(message, success=True):
    """Thread-safe progress logging with success/failure tracking"""
    with lock:
        global processed_articles, successful_predictions, failed_predictions
        processed_articles += 1
        if success:
            successful_predictions += 1
        else:
            failed_predictions += 1
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        progress_pct = (processed_articles / total_articles * 100) if total_articles > 0 else 0
        print(f"[{timestamp}] ({processed_articles}/{total_articles}, {progress_pct:.1f}%) {message}")
        
        # Log to file as well
        if success:
            logger.info(f"({processed_articles}/{total_articles}, {progress_pct:.1f}%) {message}")
        else:
            logger.error(f"({processed_articles}/{total_articles}, {progress_pct:.1f}%) {message}")

def load_api_keys():
    """Load all available Nebius API keys from environment"""
    api_keys = []
    
    # Load main key
    main_key = os.getenv('NEBIUS_API_KEY')
    if main_key and main_key.strip():
        api_keys.append(main_key.strip())
    
    # Load numbered keys (support up to 20 keys)
    for i in range(1, 21):  # Check NEBIUS_API_KEY_1 through NEBIUS_API_KEY_20
        key = os.getenv(f'NEBIUS_API_KEY_{i}')
        if key and key.strip():
            api_keys.append(key.strip())
    
    if not api_keys:
        raise ValueError("No Nebius API keys found in environment variables")
    
    # Initialize usage tracking
    with api_lock:
        for key in api_keys:
            api_key_usage[key[:8]] = 0  # Track by first 8 characters for privacy
    
    print(f"Loaded {len(api_keys)} API keys")
    logger.info(f"Loaded {len(api_keys)} API keys for parallel processing")
    return api_keys

def extract_sentiment_score(prediction_text):
    """Extract sentiment score from the prediction text with enhanced patterns"""
    try:
        import re
        
        # Pattern 1: "sentiment score: X" or "sentiment score is X"
        pattern1 = r'sentiment score(?:\s+is)?:?\s*(-?\d*\.?\d+)'
        match1 = re.search(pattern1, prediction_text.lower())
        if match1:
            score = float(match1.group(1))
            return max(-1.0, min(1.0, score))
        
        # Pattern 2: "score: X" or "score of X"
        pattern2 = r'score(?:\s+of)?:?\s*(-?\d*\.?\d+)'
        match2 = re.search(pattern2, prediction_text.lower())
        if match2:
            score = float(match2.group(1))
            return max(-1.0, min(1.0, score))
        
        # Pattern 3: Look for explicit indicators with more variations
        text_lower = prediction_text.lower()
        if 'very negative' in text_lower or 'extremely negative' in text_lower:
            return -0.9
        elif 'negative' in text_lower or 'bearish' in text_lower:
            return -0.6
        elif 'slightly negative' in text_lower or 'mildly negative' in text_lower:
            return -0.3
        elif 'very positive' in text_lower or 'extremely positive' in text_lower:
            return 0.9
        elif 'positive' in text_lower or 'bullish' in text_lower:
            return 0.6
        elif 'slightly positive' in text_lower or 'mildly positive' in text_lower:
            return 0.3
        elif 'neutral' in text_lower or 'balanced' in text_lower:
            return 0.0
        
        # Pattern 4: Look for numeric values in the text
        number_pattern = r'(-?\d*\.?\d+)'
        numbers = re.findall(number_pattern, prediction_text)
        if numbers:
            # Take the last number found as it's likely the score
            try:
                score = float(numbers[-1])
                if -1.0 <= score <= 1.0:
                    return score
            except ValueError:
                pass
        
        logger.warning(f"Could not extract sentiment score from: {prediction_text[:100]}...")
        return 0.0
        
    except Exception as e:
        logger.error(f"Error extracting sentiment score: {e}")
        return 0.0

def get_all_articles_for_prediction(client, commodity, prompt_id, days_back=None):
    """Get all sugar articles for prediction"""
    try:
        end_date = datetime.now()
        
        # Build query with optional date filtering
        date_conditions = ""
        if days_back is not None and days_back > 0:
            start_date = end_date - timedelta(days=days_back)
            date_conditions = f"AND datetime >= '{start_date.strftime('%Y-%m-%d')}'\n            "
        elif days_back == 0:
            # Special case: days_back=0 means no date filtering at all
            date_conditions = ""
        else:
            # days_back is None (default), apply no date filtering
            date_conditions = ""
        
        # Only add end date condition if we're doing date filtering
        end_date_condition = ""
        if days_back is not None and days_back > 0:
            end_date_condition = f"AND datetime <= '{end_date.strftime('%Y-%m-%d')}'"
        
        # Single query to get all sugar articles
        query = f"""
        WITH deduplicated_articles AS (
            SELECT
                id,
                title,
                text,
                source,
                asset,
                metadata,
                datetime,
                ROW_NUMBER() OVER (PARTITION BY title, source ORDER BY datetime DESC) as rn
            FROM news
            WHERE asset = '{commodity}'
            {date_conditions}{end_date_condition}
            AND length(text) > 100
        )
        SELECT
            d.id,
            d.title,
            d.text,
            d.source,
            d.asset,
            d.metadata,
            d.datetime
        FROM deduplicated_articles d
        WHERE d.rn = 1
        ORDER BY d.datetime DESC
        """
        
        result = client.execute(query)
        print(f"Found {len(result)} deduplicated sugar articles")
        logger.info(f"Found {len(result)} deduplicated sugar articles")
        return result
        
    except Exception as e:
        print(f"Error getting articles: {e}")
        logger.error(f"Error getting articles: {e}")
        return []

def predict_single_article(article_data, prompt_text, prompt_id, api_key, retry_count=3, base_delay=1.0):
    """Predict sentiment for a single article using a dedicated API instance with enhanced retry logic"""
    article_id = article_data[0] if article_data else 'unknown'
    
    for attempt in range(retry_count):
        try:
            article_id, title, text, source, asset, metadata_json, article_datetime = article_data
            
            # Track API key usage
            with api_lock:
                api_key_usage[api_key[:8]] += 1
            
            # Create dedicated API instance for this prediction
            api = NebiusAPI(api_key=api_key, timeout=120)  # Increased timeout
            
            # Parse metadata
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except:
                metadata = {}
            
            # Create formatted prompt
            formatted_prompt = prompt_text.format(
                article_title=title,
                article_text=text[:9999],  # Limit text length
                source=source,
                target_commodity=asset,
                metadata=str(metadata.get('search_topic_ids', []))
            )
            
            # Get prediction from Qwen model with enhanced parameters
            prediction = api.generate_text(
                prompt=formatted_prompt,
                model_name="Qwen/Qwen3-32B-LoRa:my-custom-model-commodity-pedw",
                max_tokens=10000,  # Increased from 1000
                temperature=0.01,   # Reduced from 0.3 for more consistent results
                max_retries=2       # Internal retries within the API client
            )
            
            if not prediction:
                if attempt < retry_count - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Retry {attempt + 1}/{retry_count} for article {article_id[:8]} after {delay:.1f}s delay")
                    time.sleep(delay)
                    continue
                log_progress(f"No prediction returned for article {article_id[:8]} after {retry_count} attempts", success=False)
                return None
            
            # Extract sentiment score
            sentiment_score = extract_sentiment_score(prediction)
            
            # Convert to enum and probabilities with enhanced logic
            if sentiment_score > 0.15:
                sentiment_enum = 'positive'
                prob_positive = min(1.0, abs(sentiment_score))
                prob_negative = 0.0
                prob_neutral = 1.0 - prob_positive
            elif sentiment_score < -0.15:
                sentiment_enum = 'negative'
                prob_negative = min(1.0, abs(sentiment_score))
                prob_positive = 0.0
                prob_neutral = 1.0 - prob_negative
            else:
                sentiment_enum = 'neutral'
                prob_neutral = 1.0 - abs(sentiment_score)
                prob_positive = max(0, sentiment_score) if sentiment_score > 0 else 0
                prob_negative = abs(min(0, sentiment_score)) if sentiment_score < 0 else 0
            
            # Normalize probabilities to ensure they sum to 1.0
            total_prob = prob_positive + prob_negative + prob_neutral
            if total_prob > 0:
                prob_positive /= total_prob
                prob_negative /= total_prob
                prob_neutral /= total_prob
            
            # Create prediction record
            prediction_record = {
                'datetime': article_datetime,
                'news_id': article_id,
                'prompt_id': prompt_id,
                'model': "Qwen/Qwen3-32B-LoRa:my-custom-model-commodity-pedw",
                'sentiment': sentiment_enum,
                'prob_negative': prob_negative,
                'prob_neutral': prob_neutral,
                'prob_positive': prob_positive,
                'created_at': datetime.now(),
                'asset': asset,  # Add asset column
                'api_key_used': api_key[:8],  # Track which key was used
                'raw_prediction': prediction[:500]  # Store first 500 chars for debugging
            }
            
            log_progress(f"Predicted {sentiment_enum} ({sentiment_score:.3f}) for {asset} article {article_id[:8]}")
            return prediction_record
            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                # Rate limit hit - wait longer
                delay = base_delay * (3 ** attempt) + random.uniform(5, 15)
                logger.warning(f"Rate limit hit for article {article_id[:8]}, retry {attempt + 1}/{retry_count} after {delay:.1f}s")
                time.sleep(delay)
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                # Timeout or connection error
                if attempt < retry_count - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                    logger.warning(f"Timeout/connection error for article {article_id[:8]}, retry {attempt + 1}/{retry_count} after {delay:.1f}s")
                    time.sleep(delay)
            else:
                # Other errors
                logger.error(f"Error predicting sentiment for article {article_id[:8]}: {error_msg}")
                if attempt == retry_count - 1:
                    break
            
            if attempt == retry_count - 1:
                log_progress(f"Failed to predict sentiment for article {article_id[:8]} after {retry_count} attempts: {error_msg}", success=False)
                return None
    
    return None

def save_predictions_batch(client, predictions, max_retries=3):
    """Save a batch of predictions to database with retry logic"""
    for attempt in range(max_retries):
        try:
            if not predictions:
                return 0
            
            records = []
            for pred in predictions:
                record = (
                    pred['datetime'],
                    pred['news_id'],
                    pred['prompt_id'],
                    pred['model'],
                    pred['sentiment'],
                    pred['prob_negative'],
                    pred['prob_neutral'],
                    pred['prob_positive'],
                    pred['created_at'],
                    pred['asset']  # Add asset column
                )
                records.append(record)
            
            client.execute(
                '''INSERT INTO sentiment_predictions
                   (datetime, news_id, prompt_id, model, sentiment,
                    prob_negative, prob_neutral, prob_positive, created_at, asset) VALUES''',
                records
            )
            
            logger.info(f"Successfully saved batch of {len(predictions)} predictions")
            return len(records)
            
        except Exception as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt + random.uniform(0, 1)
                logger.warning(f"Database save failed (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"Failed to save batch of {len(predictions)} predictions after {max_retries} attempts: {e}")
                return 0
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="Enhanced highly optimized parallel sentiment prediction for sugar")
    parser.add_argument('--commodity', type=str, default='Sugar', help='Commodity to process (default: Sugar)')
    parser.add_argument('--limit', type=int, help='Limit total articles for testing')
    parser.add_argument('--max-workers', type=int, default=30, help='Maximum concurrent workers (default: 30)')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for saving predictions (default: 50)')
    parser.add_argument('--days-back', type=int, default=None, help='Number of days back to process (default: all articles)')
    parser.add_argument('--prompt-id', type=str, default='7a603cf48e9e05d2', help='Prompt ID to use')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without executing')
    parser.add_argument('--retry-count', type=int, default=3, help='Number of retries for failed predictions (default: 3)')
    parser.add_argument('--base-delay', type=float, default=1.0, help='Base delay for exponential backoff (default: 1.0)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check if required modules are available
    if NebiusAPI is None or CLICKHOUSE_NATIVE_CONFIG is None:
        print("Error: Required modules not found. Please ensure the project structure is correct.")
        logger.error("Required modules not found")
        return
    
    # Initialize APIs and database
    try:
        api_keys = load_api_keys()
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        print("Successfully connected to Nebius APIs and ClickHouse database")
        logger.info("Successfully connected to Nebius APIs and ClickHouse database")
    except Exception as e:
        print(f"Error initializing: {e}")
        logger.error(f"Error initializing: {e}")
        return
    
    # Get prompt from database
    try:
        result = client.execute(f"SELECT prompt_text FROM prompts WHERE id = '{args.prompt_id}'")
        if not result:
            print(f"Error: Prompt with ID {args.prompt_id} not found")
            logger.error(f"Prompt with ID {args.prompt_id} not found")
            return
        prompt_text = result[0][0]
        print(f"Using prompt ID: {args.prompt_id}")
        logger.info(f"Using prompt ID: {args.prompt_id}")
    except Exception as e:
        print(f"Error getting prompt: {e}")
        logger.error(f"Error getting prompt: {e}")
        return
    
    # Get all articles
    articles = get_all_articles_for_prediction(client, args.commodity, args.prompt_id, args.days_back)
    if args.limit:
        articles = articles[:args.limit]
    
    if not articles:
        print("No articles found for processing")
        logger.warning("No articles found for processing")
        return
    
    if args.dry_run:
        print(f"\n=== DRY RUN ===")
        print(f"Would process {len(articles)} articles for {args.commodity}")
        print(f"Available API keys: {len(api_keys)}")
        print(f"Max workers: {args.max_workers}")
        print(f"Batch size: {args.batch_size}")
        return
    
    global total_articles
    total_articles = len(articles)
    
    print(f"\n=== Starting Enhanced Optimized Parallel Sentiment Prediction ===")
    print(f"Total articles to process: {total_articles}")
    print(f"Commodity: {args.commodity}")
    print(f"Max workers: {args.max_workers}")
    print(f"Batch size: {args.batch_size}")
    print(f"API keys available: {len(api_keys)}")
    print(f"Retry count: {args.retry_count}")
    print(f"Base delay: {args.base_delay}s")
    
    logger.info(f"Starting prediction for {total_articles} articles for {args.commodity}")
    
    start_time = datetime.now()
    predictions = []
    processed_count = 0
    last_save_time = start_time
    
    # Process all articles in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Create a round-robin assignment of API keys to articles
        future_to_article = {}
        
        for i, article in enumerate(articles):
            api_key = api_keys[i % len(api_keys)]  # Round-robin API key assignment
            future = executor.submit(
                predict_single_article, 
                article, 
                prompt_text, 
                args.prompt_id, 
                api_key,
                args.retry_count,
                args.base_delay
            )
            future_to_article[future] = article
        
        # Collect results and save in batches
        for future in as_completed(future_to_article):
            prediction = future.result()
            if prediction:
                predictions.append(prediction)
            
            processed_count += 1
            
            # Save predictions in batches or every 30 seconds
            current_time = datetime.now()
            if len(predictions) >= args.batch_size or (current_time - last_save_time).total_seconds() >= 30:
                if predictions:
                    saved_count = save_predictions_batch(client, predictions)
                    print(f"Saved batch of {saved_count} predictions ({processed_count}/{total_articles} processed)")
                    logger.info(f"Saved batch of {saved_count} predictions ({processed_count}/{total_articles} processed)")
                    predictions = []
                    last_save_time = current_time
    
    # Save any remaining predictions
    if predictions:
        saved_count = save_predictions_batch(client, predictions)
        print(f"Saved final batch of {saved_count} predictions")
        logger.info(f"Saved final batch of {saved_count} predictions")
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n=== SENTIMENT PREDICTION COMPLETED ===")
    print(f"Total articles processed: {processed_count}")
    print(f"Successful predictions: {successful_predictions}")
    print(f"Failed predictions: {failed_predictions}")
    print(f"Success rate: {successful_predictions/processed_count*100:.1f}%" if processed_count > 0 else "N/A")
    print(f"Total duration: {duration}")
    if processed_count > 0:
        print(f"Average time per prediction: {duration.total_seconds() / processed_count:.2f} seconds")
        print(f"Predictions per minute: {processed_count / (duration.total_seconds() / 60):.1f}")
    
    # Log API key usage statistics
    print(f"\n=== API Key Usage Statistics ===")
    with api_lock:
        for key_prefix, usage in api_key_usage.items():
            print(f"API key {key_prefix}: {usage} requests")
            logger.info(f"API key {key_prefix}: {usage} requests")
    
    logger.info(f"Prediction completed: {processed_count} articles in {duration}")

if __name__ == "__main__":
    import sys
    main()
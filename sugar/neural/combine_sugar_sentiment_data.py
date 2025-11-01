#!/usr/bin/env python3
"""
Script to combine sugar raw data from news.news with sugar predictions from sentiment_predictions
and create a unified CSV file for the period May 2021 to May 2025.
"""

import os
import sys
import csv
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from clickhouse_driver import Client
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # Go up to sugar examples root
sys.path.insert(0, str(parent_dir))

# Import the required modules
try:
    from backend.config import CLICKHOUSE_NATIVE_CONFIG
    print("Successfully imported database configuration")
except ImportError as e:
    print(f"Import attempt failed: {e}")
    CLICKHOUSE_NATIVE_CONFIG = None
    print("Import failed, setting config to None")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sugar_data_combination.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SugarDataCombiner:
    def __init__(self):
        self.client = None
        self.output_dir = Path('/Users/pauldudko/VSProjects/commodity_signal/ShinkaEvolve/shinka/examples/sugar/neural/')
        self.output_file = self.output_dir / 'sugar_sentiment_combined_may2021_may2025.csv'
        
        # Date range for extraction
        self.start_date = datetime(2021, 5, 1)
        self.end_date = datetime(2025, 5, 31)
        
        # Statistics tracking
        self.stats = {
            'raw_articles_count': 0,
            'predictions_count': 0,
            'combined_records': 0,
            'missing_predictions': 0,
            'date_range_start': None,
            'date_range_end': None,
            'quality_issues': []
        }
    
    def connect_to_database(self):
        """Connect to ClickHouse database"""
        try:
            if not CLICKHOUSE_NATIVE_CONFIG:
                raise ValueError("Database configuration not available")
            
            self.client = Client(**CLICKHOUSE_NATIVE_CONFIG)
            
            # Test connection
            result = self.client.execute('SELECT 1 as test')
            if result and result[0][0] == 1:
                logger.info("✓ ClickHouse connection successful")
                return True
            else:
                logger.error("✗ ClickHouse connection failed")
                return False
                
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
    
    def extract_sugar_raw_data(self):
        """Extract sugar raw data from news.source_of_truth table"""
        try:
            logger.info("Extracting sugar raw data from news.source_of_truth...")
            
            query = f"""
            SELECT
                timestamp_created as datetime,
                source,
                commodity as asset,
                title,
                text,
                sentiment as source_sentiment,
                confidence as source_confidence,
                events,
                timestamp_added
            FROM news.source_of_truth
            WHERE commodity = 'Sugar'
            AND timestamp_created >= '{self.start_date.strftime('%Y-%m-%d')}'
            AND timestamp_created <= '{self.end_date.strftime('%Y-%m-%d')}'
            ORDER BY timestamp_created ASC
            """
            
            result = self.client.execute(query)
            self.stats['raw_articles_count'] = len(result)
            
            # Convert to DataFrame for easier processing
            columns = ['datetime', 'source', 'asset', 'title', 'text', 'source_sentiment', 'source_confidence', 'events', 'timestamp_added']
            df = pd.DataFrame(result, columns=columns)
            
            logger.info(f"✓ Extracted {len(df)} raw sugar articles")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting raw sugar data: {e}")
            return pd.DataFrame()
    
    def extract_sentiment_predictions(self):
        """Extract sugar predictions from sentiment_predictions table"""
        try:
            logger.info("Extracting sentiment predictions...")
            
            query = f"""
            SELECT
                datetime,
                sentiment,
                prob_negative,
                prob_positive,
                prob_neutral,
                news_id
            FROM sentiment_predictions
            WHERE datetime >= '{self.start_date.strftime('%Y-%m-%d')}'
            AND datetime <= '{self.end_date.strftime('%Y-%m-%d')}'
            AND asset = 'Sugar'
            ORDER BY datetime ASC
            """
            
            result = self.client.execute(query)
            self.stats['predictions_count'] = len(result)
            
            # Convert to DataFrame
            columns = ['datetime', 'sentiment', 'prob_negative', 'prob_positive', 'prob_neutral', 'news_id']
            df = pd.DataFrame(result, columns=columns)
            
            logger.info(f"✓ Extracted {len(df)} sentiment predictions")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting sentiment predictions: {e}")
            return pd.DataFrame()
    
    def combine_data(self, raw_df, predictions_df):
        """Combine raw data with predictions using datetime and title matching"""
        try:
            logger.info("Combining raw data with predictions...")
            
            if raw_df.empty or predictions_df.empty:
                logger.warning("One or both datasets are empty")
                return pd.DataFrame()
            
            # Debug: Print column names
            logger.debug(f"Raw DataFrame columns: {raw_df.columns.tolist()}")
            logger.debug(f"Predictions DataFrame columns: {predictions_df.columns.tolist()}")
            
            # Create a unique key for matching using datetime and title
            # Round datetime to nearest minute to handle minor timestamp differences
            raw_df['datetime_rounded'] = raw_df['datetime'].dt.round('min')
            predictions_df['datetime_rounded'] = predictions_df['datetime'].dt.round('min')
            
            # Create a matching key
            raw_df['match_key'] = raw_df['datetime_rounded'].astype(str) + '_' + raw_df['title'].str[:50]
            predictions_df['match_key'] = predictions_df['datetime_rounded'].astype(str) + '_' + predictions_df['news_id'].str[:50]
            
            # Merge dataframes on the match key
            combined_df = pd.merge(
                raw_df,
                predictions_df,
                on='match_key',
                how='left',  # Keep all raw articles, even if no prediction
                suffixes=('_raw', '_pred')
            )
            
            # Use the datetime from raw data
            combined_df['datetime'] = combined_df['datetime_raw']
            
            # Select the required columns for output
            output_columns = [
                'asset', 'datetime', 'source', 'title', 'text',
                'source_sentiment', 'source_confidence',
                'sentiment', 'prob_negative', 'prob_positive', 'prob_neutral'
            ]
            
            # Check if all required columns exist
            missing_cols = [col for col in output_columns if col not in combined_df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                logger.error(f"Available columns: {combined_df.columns.tolist()}")
                return pd.DataFrame()
            
            result_df = combined_df[output_columns].copy()
            
            # Track statistics
            self.stats['combined_records'] = len(result_df)
            self.stats['missing_predictions'] = result_df['sentiment'].isna().sum()
            
            if not result_df.empty:
                self.stats['date_range_start'] = result_df['datetime'].min()
                self.stats['date_range_end'] = result_df['datetime'].max()
            
            logger.info(f"✓ Combined data: {len(result_df)} records")
            logger.info(f"  - Records with predictions: {len(result_df) - self.stats['missing_predictions']}")
            logger.info(f"  - Records missing predictions: {self.stats['missing_predictions']}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error combining data: {e}")
            logger.error(f"Raw df shape: {raw_df.shape}")
            logger.error(f"Predictions df shape: {predictions_df.shape}")
            return pd.DataFrame()
    
    def perform_data_quality_checks(self, df):
        """Perform data quality validation"""
        try:
            logger.info("Performing data quality checks...")
            
            if df.empty:
                logger.warning("Empty dataframe, skipping quality checks")
                return
            
            # Check date range
            date_mask = (df['datetime'] >= self.start_date) & (df['datetime'] <= self.end_date)
            out_of_range = len(df[~date_mask])
            if out_of_range > 0:
                issue = f"Found {out_of_range} records outside specified date range"
                self.stats['quality_issues'].append(issue)
                logger.warning(issue)
            
            # Check sentiment probabilities sum to 1.0
            prob_df = df.dropna(subset=['prob_negative', 'prob_positive', 'prob_neutral'])
            if not prob_df.empty:
                prob_sums = prob_df['prob_negative'] + prob_df['prob_positive'] + prob_df['prob_neutral']
                invalid_probs = len(prob_sums[abs(prob_sums - 1.0) > 0.01])
                if invalid_probs > 0:
                    issue = f"Found {invalid_probs} records with probabilities not summing to 1.0"
                    self.stats['quality_issues'].append(issue)
                    logger.warning(issue)
            
            # Check for missing values
            missing_sentiment = df['sentiment'].isna().sum()
            if missing_sentiment > 0:
                issue = f"Found {missing_sentiment} records missing sentiment values"
                self.stats['quality_issues'].append(issue)
                logger.warning(issue)
            
            # Check sentiment value validity
            valid_sentiments = ['positive', 'negative', 'neutral']
            invalid_sentiments = df[~df['sentiment'].isin(valid_sentiments + [np.nan])]
            if not invalid_sentiments.empty:
                issue = f"Found {len(invalid_sentiments)} records with invalid sentiment values"
                self.stats['quality_issues'].append(issue)
                logger.warning(issue)
            
            logger.info("✓ Data quality checks completed")
            
        except Exception as e:
            logger.error(f"Error performing data quality checks: {e}")
    
    def generate_csv(self, df):
        """Generate CSV file with the combined data"""
        try:
            logger.info(f"Generating CSV file: {self.output_file}")
            
            if df.empty:
                logger.warning("No data to write to CSV")
                return False
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert numeric sentiment to text for better readability
            sentiment_mapping = {1: 'positive', -1: 'negative', 0: 'neutral'}
            df['source_sentiment_text'] = df['source_sentiment'].map(sentiment_mapping)
            
            # Sort by datetime ascending
            df_sorted = df.sort_values('datetime')
            
            # Select and rename columns for final output
            final_columns = {
                'asset': 'asset',
                'datetime': 'datetime',
                'source': 'source',
                'title': 'title',
                'text': 'text',
                'source_sentiment': 'source_sentiment_numeric',
                'source_sentiment_text': 'source_sentiment',
                'source_confidence': 'source_confidence',
                'sentiment': 'predicted_sentiment',
                'prob_negative': 'prob_negative',
                'prob_neutral': 'prob_neutral',
                'prob_positive': 'prob_positive'
            }
            
            # Create final dataframe with selected columns
            final_df = df_sorted[list(final_columns.keys())].copy()
            final_df.columns = list(final_columns.values())
            
            # Write to CSV
            final_df.to_csv(
                self.output_file,
                index=False,
                encoding='utf-8',
                date_format='%Y-%m-%d %H:%M:%S'
            )
            
            # Get file size
            file_size = self.output_file.stat().st_size
            
            logger.info(f"✓ CSV file generated successfully")
            logger.info(f"  - Location: {self.output_file}")
            logger.info(f"  - Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating CSV file: {e}")
            return False
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("SUGAR SENTIMENT DATA COMBINATION SUMMARY")
        print("="*60)
        
        print(f"\n📊 DATA EXTRACTION:")
        print(f"  • Raw sugar articles: {self.stats['raw_articles_count']:,}")
        print(f"  • Sentiment predictions: {self.stats['predictions_count']:,}")
        print(f"  • Combined records: {self.stats['combined_records']:,}")
        print(f"  • Records missing predictions: {self.stats['missing_predictions']:,}")
        
        print(f"\n📅 DATE RANGE:")
        if self.stats['date_range_start'] and self.stats['date_range_end']:
            print(f"  • Start: {self.stats['date_range_start']}")
            print(f"  • End: {self.stats['date_range_end']}")
            print(f"  • Expected: {self.start_date} to {self.end_date}")
        else:
            print(f"  • Expected: {self.start_date} to {self.end_date}")
            print(f"  • Actual: No data found")
        
        print(f"\n✅ DATA QUALITY:")
        if self.stats['quality_issues']:
            print("  Issues found:")
            for issue in self.stats['quality_issues']:
                print(f"    ⚠️  {issue}")
        else:
            print("  ✓ No data quality issues detected")
        
        print(f"\n💾 OUTPUT FILE:")
        if self.output_file.exists():
            file_size = self.output_file.stat().st_size
            print(f"  • Location: {self.output_file}")
            print(f"  • Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            print(f"  • File not generated")
        
        print("\n" + "="*60)
    
    def run(self):
        """Main execution method"""
        logger.info("Starting sugar sentiment data combination process")
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
        try:
            # Extract data
            raw_df = self.extract_sugar_raw_data()
            predictions_df = self.extract_sentiment_predictions()
            
            # Combine data
            combined_df = self.combine_data(raw_df, predictions_df)
            
            # Perform quality checks
            self.perform_data_quality_checks(combined_df)
            
            # Generate CSV
            csv_success = self.generate_csv(combined_df)
            
            # Print summary
            self.print_summary()
            
            return csv_success
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            return False
        
        finally:
            # Close database connection
            if self.client:
                try:
                    self.client.disconnect()
                    logger.info("✓ Database connection closed")
                except:
                    pass

def main():
    """Main function"""
    print("Sugar Sentiment Data Combination Tool")
    print("=====================================")
    print(f"Date Range: May 2021 to May 2025")
    print(f"Output: sugar_sentiment_combined_may2021_may2025.csv")
    print()
    
    combiner = SugarDataCombiner()
    success = combiner.run()
    
    if success:
        print("\n🎉 Data combination completed successfully!")
        return 0
    else:
        print("\n❌ Data combination failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
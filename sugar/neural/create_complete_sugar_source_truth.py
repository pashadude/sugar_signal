#!/usr/bin/env python3
"""
Script to create a CSV with essential data from ALL sugar records from source_of_truth table
for the May 2021 to May 2025 time period, filtered for Dow Jones News Wire and Barrons sources.
Output: sentiment, confidence, datetime (date_added), source
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import clickhouse_connect
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # Go up to sugar examples root
sys.path.insert(0, str(parent_dir))

# Import the required modules
try:
    from backend.config import CLICKHOUSE_CONFIG
    print("Successfully imported ClickHouse config using relative path")
except ImportError as e:
    print(f"Import attempt failed: {e}")
    CLICKHOUSE_CONFIG = None
    print("Import failed, setting config to None")

def create_complete_sugar_source_truth():
    """Create CSV with ALL sugar records from source_of_truth and sentiment predictions."""
    
    print("=== Creating Complete Sugar Source of Truth Dataset (May 2021 - May 2025) ===")
    
    if CLICKHOUSE_CONFIG is None:
        print("❌ Error: ClickHouse configuration not available")
        return False
    
    try:
        # Connect to ClickHouse
        print("Connecting to ClickHouse...")
        client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
        print("✓ Connected to ClickHouse successfully")
        
        # Get essential data from ALL sugar records from source_of_truth table for May 2021 - May 2025
        # Filtered for Dow Jones News Wire and Barrons sources
        print("Getting essential data from ALL sugar records in source_of_truth table...")
        source_query = """
        SELECT
            sentiment,
            confidence,
            timestamp_added as datetime,
            source
        FROM source_of_truth
        WHERE commodity = 'Sugar'
        AND timestamp_added >= '2021-05-01'
        AND timestamp_added <= '2025-05-31'
        AND source IN ('Dow Jones News Wire', 'Barrons')
        ORDER BY timestamp_added
        """
        
        print("Executing query to extract ALL sugar records...")
        source_result = client.query(source_query)
        print(f"Found {len(source_result.result_rows)} sugar records in source_of_truth for May 2021 - May 2025")
        
        # Get column names from the result
        column_names = source_result.column_names
        print(f"Columns in result: {column_names}")
        
        # Check if we have any results
        if len(source_result.result_rows) == 0:
            print("No records found matching the criteria.")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(source_result.result_rows, columns=column_names)
        
        print(f"Final dataset has {len(df)} rows")
        print(f"Rows with sentiment: {df['sentiment'].notna().sum()}")
        print(f"Rows missing sentiment: {df['sentiment'].isna().sum()}")
        
        # Convert datetime
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        # Show summary statistics
        print(f"\n=== Summary Statistics ===")
        print(f"Source distribution:")
        print(df['source'].value_counts())
        
        print(f"Sentiment distribution:")
        if df['sentiment'].notna().sum() > 0:
            print(df['sentiment'].value_counts())
        else:
            print("No sentiment data available")
        
        if df['confidence'].notna().sum() > 0:
            print(f"\nAverage confidence: {df['confidence'].mean():.3f}")
        
        # Show first few rows
        print(f"\n=== First 3 rows ===")
        print(df.head(3))
        
        # Save to CSV with the required filename
        output_file = '/Users/pauldudko/VSProjects/commodity_signal/ShinkaEvolve/shinka/examples/sugar/neural/sugar_complete_source_truth_may2021_may2025.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n✓ CSV saved to: {output_file}")
        print(f"Total records: {len(df)}")
        
        # Get file size
        file_size = os.path.getsize(output_file)
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Close connection
        if 'client' in locals():
            client.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    success = create_complete_sugar_source_truth()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Script to check table schemas for news.source_of_truth and sentiment_predictions
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from clickhouse_driver import Client

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

def main():
    """Main function to check table schemas"""
    if not CLICKHOUSE_NATIVE_CONFIG:
        print("Database configuration not available")
        return 1
    
    client = Client(**CLICKHOUSE_NATIVE_CONFIG)
    
    try:
        # Check source_of_truth table schema
        print('=== news.source_of_truth schema ===')
        result = client.execute('DESCRIBE TABLE news.source_of_truth')
        for col in result:
            print(f'{col[0]}: {col[1]}')

        print('\n=== sentiment_predictions schema ===')
        result = client.execute('DESCRIBE TABLE sentiment_predictions')
        for col in result:
            print(f'{col[0]}: {col[1]}')
            
        # Also check a sample of data from source_of_truth
        print('\n=== Sample data from news.source_of_truth (first 3 rows) ===')
        result = client.execute('SELECT * FROM news.source_of_truth WHERE asset = \'Sugar\' LIMIT 3')
        for i, row in enumerate(result):
            print(f'Row {i+1}: {row}')
            
        # Check sample data from sentiment_predictions
        print('\n=== Sample data from sentiment_predictions (first 3 rows) ===')
        result = client.execute('SELECT * FROM sentiment_predictions LIMIT 3')
        for i, row in enumerate(result):
            print(f'Row {i+1}: {row}')
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
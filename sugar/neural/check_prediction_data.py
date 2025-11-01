#!/usr/bin/env python3
"""
Script to check the actual data in sentiment_predictions table.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import clickhouse_connect

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent  # Go up to sugar examples root
sys.path.insert(0, str(parent_dir))

# Import the required modules
try:
    from backend.config import CLICKHOUSE_CONFIG
    print("Successfully imported using relative path")
except ImportError as e:
    print(f"Import attempt failed: {e}")
    CLICKHOUSE_CONFIG = None
    print("Import failed, setting config to None")

def check_prediction_data():
    """Check the actual data in sentiment_predictions table."""
    
    print("=== Checking Prediction Data ===")
    
    if CLICKHOUSE_CONFIG is None:
        print("❌ Error: ClickHouse configuration not available")
        return False
    
    try:
        # Connect to ClickHouse
        print("Connecting to ClickHouse...")
        client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
        print("✓ Connected to ClickHouse successfully")
        
        # Check sample data from sentiment_predictions
        print("\n1. Sample data from sentiment_predictions:")
        result = client.query('SELECT * FROM sentiment_predictions LIMIT 5')
        for i, row in enumerate(result.result_rows):
            print(f"Row {i+1}: {row}")
        
        # Check data types
        print("\n2. Checking data types:")
        type_result = client.query('SELECT toTypeName(sentiment), toTypeName(prob_positive), toTypeName(prob_negative), toTypeName(prob_neutral) FROM sentiment_predictions LIMIT 1')
        if type_result.result_rows:
            sentiment_type, pos_type, neg_type, neut_type = type_result.first_row
            print(f"sentiment type: {sentiment_type}")
            print(f"prob_positive type: {pos_type}")
            print(f"prob_negative type: {neg_type}")
            print(f"prob_neutral type: {neut_type}")
        
        # Check non-zero probability values
        print("\n3. Checking for non-zero probability values:")
        non_zero_query = """
        SELECT COUNT(*) as count
        FROM sentiment_predictions
        WHERE prob_positive > 0 OR prob_negative > 0 OR prob_neutral > 0
        """
        non_zero_result = client.query(non_zero_query)
        non_zero_count = non_zero_result.first_row[0]
        print(f"Records with non-zero probabilities: {non_zero_count}")
        
        # Check value ranges
        print("\n4. Checking value ranges:")
        range_query = """
        SELECT
            MIN(prob_positive) as min_pos,
            MAX(prob_positive) as max_pos,
            MIN(prob_negative) as min_neg,
            MAX(prob_negative) as max_neg,
            MIN(prob_neutral) as min_neut,
            MAX(prob_neutral) as max_neut
        FROM sentiment_predictions
        """
        range_result = client.query(range_query)
        min_pos, max_pos, min_neg, max_neg, min_neut, max_neut = range_result.first_row
        print(f"prob_positive range: {min_pos} to {max_pos}")
        print(f"prob_negative range: {min_neg} to {max_neg}")
        print(f"prob_neutral range: {min_neut} to {max_neut}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Close connection
        if 'client' in locals():
            client.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    success = check_prediction_data()
    sys.exit(0 if success else 1)
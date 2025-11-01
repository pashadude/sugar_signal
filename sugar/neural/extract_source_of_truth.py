#!/usr/bin/env python
"""
Script to extract data from news.source_of_truth table with non-empty text fields
and save it to a CSV file for further processing.
"""

import os
import csv
from dotenv import load_dotenv
from clickhouse_driver import Client
from datetime import datetime

def extract_source_of_truth_data(output_file="source_of_truth_sugar.csv", commodity_filter="Sugar"):
    """
    Extract ALL data from news.source_of_truth table for a specific commodity,
    including records with empty text fields.
    
    Args:
        output_file: Name of the output CSV file
        commodity_filter: Filter by commodity (default: "Sugar")
    """
    # Load environment variables
    load_dotenv()

    # Get ClickHouse credentials
    clickhouse_host = os.getenv('CLICKHOUSE_HOST')
    clickhouse_user = os.getenv('CLICKHOUSE_USERNAME')
    clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')

    if not all([clickhouse_host, clickhouse_user, clickhouse_password]):
        raise ValueError("Missing required ClickHouse credentials in .env file")

    try:
        # Connect to ClickHouse
        client = Client(
            host=clickhouse_host,
            port=9000,
            user=clickhouse_user,
            password=clickhouse_password
        )

        print(f"Connected to ClickHouse. Extracting data for commodity: {commodity_filter}")

        # Build query to extract ALL data including empty text fields
        query = f"""
            SELECT
                timestamp_created,
                timestamp_added,
                commodity,
                sentiment,
                confidence,
                source,
                events,
                text,
                title
            FROM news.source_of_truth
            WHERE commodity = '{commodity_filter}'
            ORDER BY timestamp_created
        """

        print("Executing query...")
        result = client.execute(query)

        if not result:
            print("No data found matching the criteria.")
            return 0

        print(f"Found {len(result)} total records for commodity: {commodity_filter}")

        # Define CSV headers
        headers = [
            'timestamp_created', 'timestamp_added', 'commodity', 'sentiment', 
            'confidence', 'source', 'events', 'text', 'title'
        ]

        # Write to CSV file
        print(f"Writing data to {output_file}...")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for row in result:
                writer.writerow(row)

        print(f"Successfully extracted {len(result)} records to {output_file}")
        return len(result)

    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        raise

def extract_all_commodities(output_file="source_of_truth_all.csv"):
    """
    Extract data from news.source_of_truth table with non-empty text fields for all commodities.
    
    Args:
        output_file: Name of the output CSV file
    """
    # Load environment variables
    load_dotenv()

    # Get ClickHouse credentials
    clickhouse_host = os.getenv('CLICKHOUSE_HOST')
    clickhouse_user = os.getenv('CLICKHOUSE_USERNAME')
    clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')

    if not all([clickhouse_host, clickhouse_user, clickhouse_password]):
        raise ValueError("Missing required ClickHouse credentials in .env file")

    try:
        # Connect to ClickHouse
        client = Client(
            host=clickhouse_host,
            port=9000,
            user=clickhouse_user,
            password=clickhouse_password
        )

        print("Connected to ClickHouse. Extracting data for all commodities...")

        # Build query to extract data with non-empty text fields
        query = """
            SELECT 
                timestamp_created,
                timestamp_added,
                commodity,
                sentiment,
                confidence,
                source,
                events,
                text,
                title
            FROM news.source_of_truth
            WHERE text != ''
            ORDER BY timestamp_created
        """

        print("Executing query...")
        result = client.execute(query)

        if not result:
            print("No data found matching the criteria.")
            return 0

        print(f"Found {len(result)} records with non-empty text fields")

        # Define CSV headers
        headers = [
            'timestamp_created', 'timestamp_added', 'commodity', 'sentiment', 
            'confidence', 'source', 'events', 'text', 'title'
        ]

        # Write to CSV file
        print(f"Writing data to {output_file}...")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for row in result:
                writer.writerow(row)

        print(f"Successfully extracted {len(result)} records to {output_file}")
        return len(result)

    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        raise

def main():
    """Main function to extract data"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract data from news.source_of_truth table")
    parser.add_argument('--commodity', type=str, default='Sugar', 
                       help='Commodity to filter by (default: Sugar)')
    parser.add_argument('--output', type=str, default='source_of_truth_sugar.csv',
                       help='Output CSV file name (default: source_of_truth_sugar.csv)')
    parser.add_argument('--all', action='store_true',
                       help='Extract all commodities instead of filtering by one')
    
    args = parser.parse_args()
    
    if args.all:
        # Extract all commodities
        output_file = args.output if args.output != 'source_of_truth_sugar.csv' else 'source_of_truth_all.csv'
        count = extract_all_commodities(output_file)
    else:
        # Extract specific commodity
        count = extract_source_of_truth_data(args.output, args.commodity)
    
    print(f"\nExtraction completed. Total records: {count}")

if __name__ == '__main__':
    main()
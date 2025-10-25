#!/usr/bin/env python
"""
Script to create a fine-tuning dataset from news.source_of_truth table.
Extracts data for all commodities and creates JSONL files for training and evaluation.
"""

import os
import json
import random
from dotenv import load_dotenv
from clickhouse_driver import Client
from datetime import datetime

def extract_source_of_truth_data():
    """
    Extract data from news.source_of_truth table with non-empty text fields for all commodities.
    
    Returns:
        list: List of dictionaries containing the extracted data
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
            WHERE text != '' AND title != ''
            ORDER BY timestamp_created
        """

        print("Executing query...")
        result = client.execute(query)

        if not result:
            print("No data found matching the criteria.")
            return []

        print(f"Found {len(result)} records with non-empty text and title fields")

        # Convert to list of dictionaries
        data = []
        headers = [
            'timestamp_created', 'timestamp_added', 'commodity', 'sentiment', 
            'confidence', 'source', 'events', 'text', 'title'
        ]
        
        for row in result:
            data.append(dict(zip(headers, row)))

        print(f"Successfully extracted {len(data)} records")
        return data

    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        raise

def create_finetuning_records(data):
    """
    Create fine-tuning records with the specified prompt format.
    
    Args:
        data: List of dictionaries containing the extracted data
        
    Returns:
        list: List of dictionaries in the fine-tuning format
    """
    finetuning_records = []
    max_sequence_length = 8192
    skipped_records = 0
    
    for record in data:
        # Create the completion with sentiment and confidence
        completion = f"Sentiment: {record['sentiment']}, Confidence: {record['confidence']}"
        
        # Calculate available space for text
        base_prompt = f"you are a commodity trader trading {record['commodity']}, you got news {record['title']} about events {record['events']} - please analyse their text TEXT_PLACEHOLDER and provide sentiment (1- positive, 0- neutral, -1 -neagarive) with confidence from 0 to 1"
        available_space = max_sequence_length - len(base_prompt) - len(completion)
        
        # If available space is too small, skip this record
        if available_space < 100:  # Minimum reasonable text length
            skipped_records += 1
            continue
        
        # Trim text to fit within available space
        text = record['text']
        if len(text) > available_space:
            # Try to trim at a sentence boundary
            trimmed_text = text[:available_space]
            # Look for the last sentence boundary
            last_period = trimmed_text.rfind('.')
            last_exclamation = trimmed_text.rfind('!')
            last_question = trimmed_text.rfind('?')
            
            # Find the last sentence boundary
            last_boundary = max(last_period, last_exclamation, last_question)
            
            if last_boundary > available_space * 0.7:  # If we can keep at least 70% of the text
                text = trimmed_text[:last_boundary + 1]
            else:
                # Just truncate at the available space
                text = trimmed_text
        
        # Create the final prompt with trimmed text
        prompt = f"you are a commodity trader trading {record['commodity']}, you got news {record['title']} about events {record['events']} - please analyse their text {text} and provide sentiment (1- positive, 0- neutral, -1 -neagarive) with confidence from 0 to 1"
        
        # Double-check total length
        total_length = len(prompt) + len(completion)
        if total_length > max_sequence_length:
            # Further trim text if needed
            excess = total_length - max_sequence_length
            text = text[:-excess]
            prompt = f"you are a commodity trader trading {record['commodity']}, you got news {record['title']} about events {record['events']} - please analyse their text {text} and provide sentiment (1- positive, 0- neutral, -1 -neagarive) with confidence from 0 to 1"
        
        # Create the fine-tuning record
        finetuning_record = {
            "prompt": prompt,
            "completion": completion
        }
        
        finetuning_records.append(finetuning_record)
    
    print(f"Created {len(finetuning_records)} fine-tuning records")
    if skipped_records > 0:
        print(f"Skipped {skipped_records} records due to length constraints")
    
    return finetuning_records

def split_dataset(data, eval_ratio=0.15):
    """
    Split the dataset into training and evaluation sets.
    
    Args:
        data: List of records to split
        eval_ratio: Ratio of data to use for evaluation (default: 0.15)
        
    Returns:
        tuple: (train_data, eval_data)
    """
    # Set random seed for reproducibility
    random.seed(42)
    
    # Shuffle the data
    shuffled_data = data.copy()
    random.shuffle(shuffled_data)
    
    # Calculate split point
    split_index = int(len(shuffled_data) * (1 - eval_ratio))
    
    # Split the data
    train_data = shuffled_data[:split_index]
    eval_data = shuffled_data[split_index:]
    
    print(f"Split dataset:")
    print(f"  Training: {len(train_data)} records ({len(train_data)/len(data)*100:.1f}%)")
    print(f"  Evaluation: {len(eval_data)} records ({len(eval_data)/len(data)*100:.1f}%)")
    
    return train_data, eval_data

def save_jsonl(data, filename):
    """
    Save data to a JSONL file.
    
    Args:
        data: List of dictionaries to save
        filename: Name of the output file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"Saved {len(data)} records to {filename}")

def main():
    """Main function to create the fine-tuning dataset"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create fine-tuning dataset from news.source_of_truth table")
    parser.add_argument('--train-output', type=str, default='train.jsonl',
                       help='Output JSONL file for training (default: train.jsonl)')
    parser.add_argument('--eval-output', type=str, default='eval.jsonl',
                       help='Output JSONL file for evaluation (default: eval.jsonl)')
    parser.add_argument('--eval-ratio', type=float, default=0.15,
                       help='Ratio of data to use for evaluation (default: 0.15)')
    
    args = parser.parse_args()
    
    print("Creating fine-tuning dataset from news.source_of_truth table...")
    
    # Step 1: Extract data from database
    print("\nStep 1: Extracting data from database...")
    raw_data = extract_source_of_truth_data()
    
    if not raw_data:
        print("No data found. Exiting.")
        return
    
    # Step 2: Create fine-tuning records
    print("\nStep 2: Creating fine-tuning records...")
    finetuning_data = create_finetuning_records(raw_data)
    
    # Step 3: Split into training and evaluation sets
    print("\nStep 3: Splitting dataset...")
    train_data, eval_data = split_dataset(finetuning_data, args.eval_ratio)
    
    # Step 4: Save to JSONL files
    print("\nStep 4: Saving to JSONL files...")
    save_jsonl(train_data, args.train_output)
    save_jsonl(eval_data, args.eval_output)
    
    # Print sample records
    print("\nSample training record:")
    print(json.dumps(train_data[0], indent=2, ensure_ascii=False))
    
    print("\nSample evaluation record:")
    print(json.dumps(eval_data[0], indent=2, ensure_ascii=False))
    
    print(f"\nFine-tuning dataset creation completed!")
    print(f"Training file: {args.train_output} ({len(train_data)} records)")
    print(f"Evaluation file: {args.eval_output} ({len(eval_data)} records)")

if __name__ == '__main__':
    main()
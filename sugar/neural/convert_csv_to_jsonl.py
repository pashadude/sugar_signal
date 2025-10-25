#!/usr/bin/env python
"""
Script to convert source_of_truth_sugar.csv to JSONL format and create a validation dataset.
"""

import csv
import json
import random
import os
from pathlib import Path

def convert_csv_to_jsonl(csv_file_path, output_dir):
    """
    Convert CSV file to JSONL format and split into training and validation datasets.
    
    Args:
        csv_file_path: Path to the input CSV file
        output_dir: Directory to save the output JSONL files
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Read CSV file
    print(f"Reading CSV file: {csv_file_path}")
    data = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        # Try to detect the delimiter
        sample = csvfile.read(1024)
        csvfile.seek(0)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
        
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        for row in reader:
            data.append(row)
    
    print(f"Loaded {len(data)} records from CSV")
    
    # Shuffle the data for random splitting
    random.shuffle(data)
    
    # Split into training (80%) and validation (20%)
    split_index = int(len(data) * 0.8)
    train_data = data[:split_index]
    val_data = data[split_index:]
    
    print(f"Split data into:")
    print(f"  Training: {len(train_data)} records (80%)")
    print(f"  Validation: {len(val_data)} records (20%)")
    
    # Write training data to JSONL
    train_file = os.path.join(output_dir, 'train.jsonl')
    with open(train_file, 'w', encoding='utf-8') as f:
        for record in train_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"Training data saved to: {train_file}")
    
    # Write validation data to JSONL
    val_file = os.path.join(output_dir, 'val.jsonl')
    with open(val_file, 'w', encoding='utf-8') as f:
        for record in val_data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"Validation data saved to: {val_file}")
    
    # Print sample records
    print("\nSample training record:")
    print(json.dumps(train_data[0], indent=2, ensure_ascii=False))
    
    print("\nSample validation record:")
    print(json.dumps(val_data[0], indent=2, ensure_ascii=False))
    
    return train_file, val_file

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    
    # File paths
    csv_file = "source_of_truth_sugar.csv"
    output_directory = "."
    
    # Convert CSV to JSONL
    train_file, val_file = convert_csv_to_jsonl(csv_file, output_directory)
    
    print("\nConversion completed successfully!")
    print(f"Training file: {train_file}")
    print(f"Validation file: {val_file}")
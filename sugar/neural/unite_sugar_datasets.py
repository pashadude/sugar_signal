import pandas as pd
import os

def unite_sugar_datasets():
    """
    Unite two CSV files and create a clean final dataset with specific columns.
    
    Files to unite:
    1. sugar_complete_source_truth_may2021_may2025.csv (382,028 records)
    2. sugar_united_dataset.csv (705 records)
    
    Output: sugar_final_united_dataset.csv with columns: datetime, sentiment, confidence
    """
    
    # Define file paths
    file1_path = "sugar_complete_source_truth_may2021_may2025.csv"
    file2_path = "sugar_united_dataset.csv"
    output_path = "sugar_final_united_dataset.csv"
    
    print("Starting to unite sugar datasets...")
    
    try:
        # Read the first CSV file
        print(f"Reading {file1_path}...")
        df1 = pd.read_csv(file1_path)
        print(f"File 1 loaded successfully with {len(df1)} records")
        
        # Read the second CSV file
        print(f"Reading {file2_path}...")
        df2 = pd.read_csv(file2_path)
        print(f"File 2 loaded successfully with {len(df2)} records")
        
        # Display column names for debugging
        print(f"File 1 columns: {df1.columns.tolist()}")
        print(f"File 2 columns: {df2.columns.tolist()}")
        
        # Extract required columns from first file
        required_columns = ['datetime', 'sentiment', 'confidence']
        
        # Check if required columns exist in both files
        for col in required_columns:
            if col not in df1.columns:
                print(f"Warning: Column '{col}' not found in file 1")
            if col not in df2.columns:
                print(f"Warning: Column '{col}' not found in file 2")
        
        # Extract only the required columns
        df1_extracted = df1[required_columns].copy()
        df2_extracted = df2[required_columns].copy()
        
        print(f"Extracted columns from file 1: {len(df1_extracted)} records")
        print(f"Extracted columns from file 2: {len(df2_extracted)} records")
        
        # Combine datasets
        print("Combining datasets...")
        combined_df = pd.concat([df1_extracted, df2_extracted], ignore_index=True)
        print(f"Combined dataset has {len(combined_df)} records before removing duplicates")
        
        # Remove duplicates based on all three columns
        print("Removing duplicates...")
        combined_df = combined_df.drop_duplicates(subset=required_columns, keep='first')
        print(f"Dataset has {len(combined_df)} records after removing duplicates")
        
        # Convert datetime column to datetime format for proper sorting
        print("Converting datetime format...")
        # Use mixed format with UTC=True to handle different datetime formats and timezones
        combined_df['datetime'] = pd.to_datetime(combined_df['datetime'], format='mixed', utc=True)
        
        # Sort by datetime in ascending order
        print("Sorting by datetime...")
        combined_df = combined_df.sort_values('datetime', ascending=True)
        
        # Convert datetime back to string format for output (remove timezone info)
        combined_df['datetime'] = combined_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to new CSV file
        print(f"Saving to {output_path}...")
        combined_df.to_csv(output_path, index=False)
        
        print(f"Successfully created unified dataset with {len(combined_df)} records")
        print(f"Output saved to: {output_path}")
        
        # Display sample of the final dataset
        print("\nSample of the final dataset:")
        print(combined_df.head())
        
        # Display dataset info
        print("\nDataset info:")
        print(f"Date range: {combined_df['datetime'].min()} to {combined_df['datetime'].max()}")
        print(f"Unique sentiment values: {combined_df['sentiment'].unique()}")
        print(f"Confidence range: {combined_df['confidence'].min():.4f} to {combined_df['confidence'].max():.4f}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    unite_sugar_datasets()
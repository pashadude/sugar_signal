#!/usr/bin/env python
"""
Test script for checkpoint functionality in sugar_news_fetcher.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import (
    save_intermediate_results,
    load_intermediate_results,
    cleanup_checkpoint_files,
    save_checkpoint,
    load_checkpoint
)

def test_checkpoint_functions():
    """Test the checkpoint-related functions"""
    print("Testing checkpoint functionality...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Test data
        test_data = [
            {"id": 1, "title": "Test Article 1", "content": "Test content 1"},
            {"id": 2, "title": "Test Article 2", "content": "Test content 2"},
            {"id": 3, "title": "Test Article 3", "content": "Test content 3"}
        ]
        
        # Test save_intermediate_results
        print("\n1. Testing save_intermediate_results...")
        save_success = save_intermediate_results(test_data, 1, temp_dir)
        assert save_success, "Failed to save intermediate results"
        print("✓ save_intermediate_results works correctly")
        
        # Test load_intermediate_results
        print("\n2. Testing load_intermediate_results...")
        loaded_data = load_intermediate_results(temp_dir)
        assert len(loaded_data) == len(test_data), "Loaded data length doesn't match original"
        assert loaded_data == test_data, "Loaded data doesn't match original"
        print("✓ load_intermediate_results works correctly")
        
        # Test save_checkpoint and load_checkpoint
        print("\n3. Testing save_checkpoint and load_checkpoint...")
        checkpoint_file = os.path.join(temp_dir, "test_checkpoint.pkl")
        checkpoint_data = {"batch": 1, "processed": 10, "failed": 2}
        
        save_success = save_checkpoint(checkpoint_data, checkpoint_file)
        assert save_success, "Failed to save checkpoint"
        print("✓ save_checkpoint works correctly")
        
        loaded_checkpoint = load_checkpoint(checkpoint_file)
        assert loaded_checkpoint == checkpoint_data, "Loaded checkpoint doesn't match original"
        print("✓ load_checkpoint works correctly")
        
        # Test cleanup_checkpoint_files
        print("\n4. Testing cleanup_checkpoint_files...")
        cleanup_success = cleanup_checkpoint_files(temp_dir)
        assert cleanup_success, "Failed to cleanup checkpoint files"
        
        # Verify files are cleaned up
        remaining_files = [f for f in os.listdir(temp_dir) if f.startswith("intermediate_results_batch_")]
        assert len(remaining_files) == 0, "Checkpoint files were not cleaned up"
        print("✓ cleanup_checkpoint_files works correctly")
        
        print("\n✅ All checkpoint functionality tests passed!")

def test_resume_functionality():
    """Test the resume functionality with mock data"""
    print("\nTesting resume functionality...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Create mock dataframes (simulating what would be saved during processing)
        import pandas as pd
        
        mock_df1 = pd.DataFrame([
            {"id": "1", "title": "Article 1", "asset": "Sugar"},
            {"id": "2", "title": "Article 2", "asset": "Sugar"}
        ])
        
        mock_df2 = pd.DataFrame([
            {"id": "3", "title": "Article 3", "asset": "Sugar"},
            {"id": "4", "title": "Article 4", "asset": "General"}
        ])
        
        # Save intermediate results in batches
        print("\n1. Saving mock intermediate results...")
        save_success1 = save_intermediate_results([mock_df1], 1, temp_dir)
        save_success2 = save_intermediate_results([mock_df1, mock_df2], 2, temp_dir)
        
        assert save_success1 and save_success2, "Failed to save mock intermediate results"
        print("✓ Mock intermediate results saved successfully")
        
        # Test loading intermediate results (simulating resume)
        print("\n2. Testing resume by loading intermediate results...")
        loaded_results = load_intermediate_results(temp_dir)
        
        # Verify loaded results
        assert len(loaded_results) == 3, "Should have 3 total articles (2 from first batch, 1 new from second)"
        assert len(loaded_results[0]) == 2, "First dataframe should have 2 articles"
        assert len(loaded_results[1]) == 2, "Second dataframe should have 2 articles"
        print("✓ Resume functionality works correctly")
        
        # Test cleanup
        print("\n3. Testing cleanup after resume...")
        cleanup_success = cleanup_checkpoint_files(temp_dir)
        assert cleanup_success, "Failed to cleanup after resume"
        print("✓ Cleanup after resume works correctly")
        
        print("\n✅ All resume functionality tests passed!")

def test_error_handling():
    """Test error handling for checkpoint functions"""
    print("\nTesting error handling...")
    
    # Test with non-existent directory
    print("\n1. Testing with non-existent directory...")
    non_existent_dir = "/tmp/non_existent_directory_12345"
    loaded_data = load_intermediate_results(non_existent_dir)
    assert loaded_data == [], "Should return empty list for non-existent directory"
    print("✓ Handles non-existent directory correctly")
    
    # Test cleanup of non-existent directory
    cleanup_success = cleanup_checkpoint_files(non_existent_dir)
    assert cleanup_success, "Should return True for non-existent directory"
    print("✓ Handles cleanup of non-existent directory correctly")
    
    # Test with invalid checkpoint file
    print("\n2. Testing with invalid checkpoint file...")
    with tempfile.TemporaryDirectory() as temp_dir:
        invalid_file = os.path.join(temp_dir, "invalid_checkpoint.pkl")
        
        # Create an invalid pickle file
        with open(invalid_file, 'w') as f:
            f.write("This is not a valid pickle file")
        
        loaded_checkpoint = load_checkpoint(invalid_file)
        assert loaded_checkpoint is None, "Should return None for invalid checkpoint file"
        print("✓ Handles invalid checkpoint file correctly")
    
    print("\n✅ All error handling tests passed!")

if __name__ == "__main__":
    try:
        test_checkpoint_functions()
        test_resume_functionality()
        test_error_handling()
        print("\n🎉 All tests passed! The checkpoint functionality is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)
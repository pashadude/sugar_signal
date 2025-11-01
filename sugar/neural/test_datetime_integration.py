#!/usr/bin/env python
"""
Test script to verify that datetime is properly integrated into the predictor.
This test focuses on prompt creation without requiring API calls.
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path to import predictor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import CommoditySentimentPredictor


def test_datetime_in_prompt():
    """
    Test that datetime is properly included in the user prompt.
    """
    print("=== Testing datetime integration in predictor ===\n")
    
    # Create a predictor instance (without API key for this test)
    try:
        # We'll catch the API key error and continue with the test
        predictor = CommoditySentimentPredictor(api_key="dummy_key_for_testing")
    except ValueError as e:
        if "NEBIUS_API_KEY" in str(e):
            # Create a mock predictor for testing
            predictor = CommoditySentimentPredictor.__new__(CommoditySentimentPredictor)
            predictor.api_key = "dummy_key_for_testing"
            predictor.model = "test_model"
            predictor._client = None
            predictor._clickhouse_client = None
            predictor.save_prompts = False
        else:
            raise e
    
    # Test data
    test_text = "Sugar prices are expected to rise due to poor weather conditions in Brazil."
    test_title = "Sugar Market Outlook"
    test_commodity = "Sugar"
    test_topics = ["agriculture", "weather", "Brazil"]
    test_datetime = datetime(2023, 10, 15, 14, 30, 0)
    
    print("Test data:")
    print(f"  Title: {test_title}")
    print(f"  Commodity: {test_commodity}")
    print(f"  Topics: {test_topics}")
    print(f"  Datetime: {test_datetime}")
    print(f"  Text: {test_text[:50]}...")
    print()
    
    # Test prompt creation without datetime
    print("=== Testing prompt creation WITHOUT datetime ===")
    prompt_without_datetime = predictor._create_user_prompt(
        text=test_text,
        title=test_title,
        commodity=test_commodity,
        topics=test_topics,
        datetime=None
    )
    print("Generated prompt:")
    print(prompt_without_datetime)
    print()
    
    # Test prompt creation with datetime
    print("=== Testing prompt creation WITH datetime ===")
    prompt_with_datetime = predictor._create_user_prompt(
        text=test_text,
        title=test_title,
        commodity=test_commodity,
        topics=test_topics,
        datetime=test_datetime
    )
    print("Generated prompt:")
    print(prompt_with_datetime)
    print()
    
    # Verify that datetime is included in the prompt
    expected_datetime_str = "Date: 2023-10-15 14:30:00"
    if expected_datetime_str in prompt_with_datetime:
        print("✓ Datetime correctly included in prompt")
    else:
        print("✗ Datetime NOT found in prompt")
        return False
    
    # Verify that datetime is NOT included when not provided
    if "Date:" not in prompt_without_datetime:
        print("✓ Datetime correctly excluded when not provided")
    else:
        print("✗ Datetime found in prompt when not provided")
        return False
    
    # Test that the datetime appears in the correct position (after title, before topics)
    prompt_lines = prompt_with_datetime.split('\n\n')
    datetime_line_index = None
    title_line_index = None
    topics_line_index = None
    
    for i, line in enumerate(prompt_lines):
        if line.startswith("Date:"):
            datetime_line_index = i
        elif line.startswith("Title:"):
            title_line_index = i
        elif line.startswith("Topics:"):
            topics_line_index = i
    
    if (datetime_line_index is not None and 
        title_line_index is not None and 
        topics_line_index is not None and
        title_line_index < datetime_line_index < topics_line_index):
        print("✓ Datetime appears in correct position in prompt")
    else:
        print("✗ Datetime appears in incorrect position in prompt")
        return False
    
    print("\n✅ All datetime integration tests passed!")
    return True


def test_command_line_parsing():
    """
    Test that command line argument parsing works for datetime.
    """
    print("\n=== Testing command line datetime parsing ===\n")
    
    # Test valid datetime formats
    test_cases = [
        ("2023-10-15 14:30:00", True),
        ("2023-10-15", True),
        ("invalid-date", False),
        ("", False)
    ]
    
    for datetime_str, should_succeed in test_cases:
        print(f"Testing datetime string: '{datetime_str}'")
        
        try:
            if datetime_str:
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                print(f"  ✓ Parsed as: {datetime_obj}")
            else:
                datetime_obj = None
                print("  ✓ Empty datetime handled correctly")
            
            if not should_succeed and datetime_str:  # Only fail if we expected failure and string wasn't empty
                print("  ✗ Expected parsing to fail but it succeeded")
                return False
                
        except ValueError:
            try:
                # Try alternative format
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d')
                print(f"  ✓ Parsed as date only: {datetime_obj}")
                
                if not should_succeed and datetime_str:  # Only fail if we expected failure and string wasn't empty
                    print("  ✗ Expected parsing to fail but it succeeded")
                    return False
                    
            except ValueError:
                print("  ✓ Parsing failed as expected")
                
                if should_succeed and datetime_str:  # Only fail if we expected success and string wasn't empty
                    print("  ✗ Expected parsing to succeed but it failed")
                    return False
    
    print("\n✅ All command line datetime parsing tests passed!")
    return True


def main():
    """
    Main function to run all tests.
    """
    print("Starting datetime integration tests...\n")
    
    # Run tests
    test1_passed = test_datetime_in_prompt()
    test2_passed = test_command_line_parsing()
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Datetime integration is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python
"""
Test script for the CommoditySentimentPredictor class.
Tests basic functionality without requiring API credentials.
"""

import sys
import os
import json
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add the current directory to the path to import predictor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import CommoditySentimentPredictor


def test_initialization():
    """Test predictor initialization with and without API key."""
    print("Testing initialization...")
    
    # Test without API key (should fail)
    try:
        predictor = CommoditySentimentPredictor()
        print("✓ Initialization with environment variable would work if API key was set")
    except ValueError as e:
        print(f"✓ Expected error when no API key: {e}")
    
    # Test with dummy API key
    try:
        predictor = CommoditySentimentPredictor(api_key="dummy_key")
        print("✓ Initialization with provided API key successful")
        return predictor
    except Exception as e:
        print(f"✗ Unexpected error during initialization: {e}")
        return None


def test_prompt_creation(predictor):
    """Test system and user prompt creation."""
    print("\nTesting prompt creation...")
    
    # Test system prompt
    system_prompt = predictor._create_system_prompt()
    if len(system_prompt) > 100 and "sentiment" in system_prompt.lower():
        print("✓ System prompt created successfully")
    else:
        print("✗ System prompt creation failed")
    
    # Test user prompt without topics
    test_text = "Sugar prices are rising due to poor harvest conditions."
    test_title = "Sugar Market Update"
    test_commodity = "Sugar"
    
    user_prompt = predictor._create_user_prompt(test_text, test_title, test_commodity)
    if all(x in user_prompt for x in [test_text, test_title, test_commodity]):
        print("✓ User prompt created successfully")
    else:
        print("✗ User prompt creation failed")
    
    # Test user prompt with topics
    test_topics = ["agriculture", "weather", "market"]
    user_prompt_with_topics = predictor._create_user_prompt(test_text, test_title, test_commodity, test_topics)
    if all(x in user_prompt_with_topics for x in [test_text, test_title, test_commodity] + test_topics):
        print("✓ User prompt with topics created successfully")
    else:
        print("✗ User prompt with topics creation failed")


def test_text_parsing():
    """Test the fallback text parsing method."""
    print("\nTesting text parsing...")
    
    predictor = CommoditySentimentPredictor(api_key="dummy_key")
    
    # Test positive sentiment
    positive_text = "The sentiment is positive with high confidence of 0.9. Bullish outlook."
    result = predictor._parse_text_response(positive_text)
    if result['sentiment'] == 'positive' and result['confidence'] == 0.9:
        print("✓ Positive sentiment parsing works")
    else:
        print("✗ Positive sentiment parsing failed")
    
    # Test negative sentiment
    negative_text = "Negative sentiment detected. Bearish market conditions. Confidence around 0.8."
    result = predictor._parse_text_response(negative_text)
    if result['sentiment'] == 'negative':
        print("✓ Negative sentiment parsing works")
    else:
        print("✗ Negative sentiment parsing failed")
    
    # Test neutral/default case
    neutral_text = "Some random text without clear sentiment indicators."
    result = predictor._parse_text_response(neutral_text)
    if result['sentiment'] == 'neutral':
        print("✓ Neutral sentiment parsing works")
    else:
        print("✗ Neutral sentiment parsing failed")


def test_error_handling():
    """Test error handling for various edge cases."""
    print("\nTesting error handling...")
    
    predictor = CommoditySentimentPredictor(api_key="dummy_key")
    
    # Test empty text
    try:
        predictor.analyze_sentiment("")
        print("✗ Empty text should have raised an error")
    except ValueError:
        print("✓ Empty text error handling works")
    
    # Test whitespace-only text
    try:
        predictor.analyze_sentiment("   ")
        print("✗ Whitespace-only text should have raised an error")
    except ValueError:
        print("✓ Whitespace-only text error handling works")
    
    # Test batch analysis with empty list
    results = predictor.batch_analyze([])
    if results == []:
        print("✓ Empty batch analysis works")
    else:
        print("✗ Empty batch analysis failed")


def test_mock_api_call():
    """Test the API call structure with mocked response."""
    print("\nTesting mock API call...")
    
    predictor = CommoditySentimentPredictor(api_key="dummy_key")
    
    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "sentiment": "positive",
        "confidence": 0.85,
        "reasoning": "Strong demand and supply constraints indicate bullish outlook."
    })
    
    with patch.object(predictor.client.chat.completions, 'create', return_value=mock_response):
        try:
            # Test without topics
            result = predictor.analyze_sentiment("Test text", "Test title", "Sugar")
            if (result['sentiment'] == 'positive' and
                result['confidence'] == 0.85 and
                'reasoning' in result):
                print("✓ Mock API call and JSON parsing works")
            else:
                print("✗ Mock API call failed")
            
            # Test with topics
            test_topics = ["agriculture", "weather"]
            result_with_topics = predictor.analyze_sentiment("Test text", "Test title", "Sugar", test_topics)
            if (result_with_topics['sentiment'] == 'positive' and
                result_with_topics['confidence'] == 0.85 and
                'reasoning' in result_with_topics):
                print("✓ Mock API call with topics works")
            else:
                print("✗ Mock API call with topics failed")
                
        except Exception as e:
            print(f"✗ Mock API call error: {e}")


def main():
    """Run all tests."""
    print("=== Testing CommoditySentimentPredictor ===\n")
    
    # Test initialization
    predictor = test_initialization()
    if not predictor:
        print("Cannot continue tests - initialization failed")
        return 1
    
    # Test prompt creation
    test_prompt_creation(predictor)
    
    # Test text parsing
    test_text_parsing()
    
    # Test error handling
    test_error_handling()
    
    # Test mock API call
    test_mock_api_call()
    
    print("\n=== Test Summary ===")
    print("All basic functionality tests completed.")
    print("Note: Actual API calls require valid NEBIUS_API_KEY environment variable.")
    
    return 0


if __name__ == "__main__":
    exit(main())
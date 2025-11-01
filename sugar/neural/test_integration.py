#!/usr/bin/env python
"""
Integration test for the CommoditySentimentPredictor class.
Tests actual API calls with the Qwen model.
"""

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Add the current directory to the path to import predictor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import CommoditySentimentPredictor


def test_real_api_call():
    """Test actual API call with the Qwen model."""
    print("=== Testing Real API Call ===")
    
    # Check if API key is available
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        print("❌ NEBIUS_API_KEY not found in environment variables")
        return False
    
    print("✓ API key found")
    
    try:
        # Initialize predictor
        predictor = CommoditySentimentPredictor(api_key=api_key)
        print("✓ Predictor initialized successfully")
        
        # Test with a simple commodity news text
        test_text = """
        Sugar prices surged to a three-month high as concerns over supply disruptions 
        from major producing countries grew. Unfavorable weather conditions in Brazil 
        and India have raised fears of a global supply shortage, while demand remains 
        strong from Asian markets. Traders are optimistic about the market outlook 
        for the coming quarter.
        """
        
        test_title = "Sugar Prices Reach Three-Month High on Supply Concerns"
        test_commodity = "Sugar"
        
        print(f"📝 Analyzing text: {test_text[:100]}...")
        
        # Perform sentiment analysis without topics
        result = predictor.analyze_sentiment(test_text, test_title, test_commodity)
        
        print("\n📊 Analysis Results (without topics):")
        print(f"   Sentiment: {result['sentiment']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Reasoning: {result['reasoning']}")
        
        # Validate result structure
        required_fields = ['sentiment', 'confidence', 'reasoning']
        if all(field in result for field in required_fields):
            print("✓ All required fields present in response")
        else:
            print("❌ Missing required fields in response")
            return False
        
        # Validate sentiment value
        if result['sentiment'] in ['positive', 'negative', 'neutral']:
            print("✓ Valid sentiment value")
        else:
            print(f"❌ Invalid sentiment value: {result['sentiment']}")
            return False
        
        # Validate confidence range
        if 0.0 <= result['confidence'] <= 1.0:
            print("✓ Valid confidence range")
        else:
            print(f"❌ Invalid confidence range: {result['confidence']}")
            return False
        
        # Test with topics
        test_topics = ["agriculture", "weather", "market"]
        print(f"\n📝 Analyzing text with topics: {', '.join(test_topics)}...")
        
        result_with_topics = predictor.analyze_sentiment(test_text, test_title, test_commodity, test_topics)
        
        print("\n📊 Analysis Results (with topics):")
        print(f"   Sentiment: {result_with_topics['sentiment']}")
        print(f"   Confidence: {result_with_topics['confidence']:.2f}")
        print(f"   Reasoning: {result_with_topics['reasoning']}")
        
        # Validate result with topics
        if all(field in result_with_topics for field in required_fields):
            print("✓ All required fields present in response with topics")
        else:
            print("❌ Missing required fields in response with topics")
            return False
        
        print("\n✅ Real API call test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during API call: {str(e)}")
        return False


def test_batch_analysis():
    """Test batch analysis functionality."""
    print("\n=== Testing Batch Analysis ===")
    
    try:
        predictor = CommoditySentimentPredictor()
        
        # Test texts
        texts = [
            "Sugar prices fell due to increased production and weak demand.",
            "The sugar market remains stable with balanced supply and demand.",
            "Positive outlook for sugar as demand exceeds supply expectations."
        ]
        
        titles = [
            "Sugar Prices Decline on Production Surge",
            "Sugar Market Stability Continues",
            "Sugar Demand Exceeds Supply Forecasts"
        ]
        
        commodities = ["Sugar"] * 3
        
        print(f"📝 Analyzing {len(texts)} texts in batch...")
        
        # Test batch analysis without topics
        results = predictor.batch_analyze(texts, titles, commodities)
        
        print(f"\n📊 Batch Analysis Results (without topics):")
        for i, result in enumerate(results):
            print(f"   Text {i+1}: {result['sentiment']} (confidence: {result['confidence']:.2f})")
        
        if len(results) != len(texts):
            print("❌ Batch analysis failed - incorrect number of results")
            return False
        
        # Test batch analysis with topics
        topics_list = [
            ["production", "supply"],
            ["market", "stability"],
            ["demand", "forecast"]
        ]
        
        print(f"\n📝 Analyzing {len(texts)} texts in batch with topics...")
        
        results_with_topics = predictor.batch_analyze(texts, titles, commodities, topics_list)
        
        print(f"\n📊 Batch Analysis Results (with topics):")
        for i, result in enumerate(results_with_topics):
            print(f"   Text {i+1}: {result['sentiment']} (confidence: {result['confidence']:.2f})")
        
        if len(results_with_topics) == len(texts):
            print("✓ Batch analysis completed successfully")
            return True
        else:
            print("❌ Batch analysis with topics failed - incorrect number of results")
            return False
            
    except Exception as e:
        print(f"❌ Error during batch analysis: {str(e)}")
        return False


def main():
    """Run integration tests."""
    print("=== CommoditySentimentPredictor Integration Tests ===\n")
    
    # Test real API call
    api_test_passed = test_real_api_call()
    
    # Test batch analysis
    batch_test_passed = test_batch_analysis()
    
    print("\n=== Integration Test Summary ===")
    print(f"Real API Call: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    print(f"Batch Analysis: {'✅ PASSED' if batch_test_passed else '❌ FAILED'}")
    
    if api_test_passed and batch_test_passed:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
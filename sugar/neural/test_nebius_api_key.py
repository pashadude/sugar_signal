#!/usr/bin/env python
"""
Test script to verify that the NEBIUS_API_KEY environment variable is correctly retrieved
by the CommoditySentimentPredictor class.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add the current directory to the path to import predictor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictor import CommoditySentimentPredictor


class TestNebiusAPIKeyRetrieval(unittest.TestCase):
    """Test cases for NEBIUS_API_KEY retrieval from environment variables."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment variable if it exists
        self.original_api_key = os.environ.get("NEBIUS_API_KEY")
        
    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variable
        if self.original_api_key is not None:
            os.environ["NEBIUS_API_KEY"] = self.original_api_key
        elif "NEBIUS_API_KEY" in os.environ:
            del os.environ["NEBIUS_API_KEY"]

    def test_api_key_from_environment(self):
        """Test that API key is correctly retrieved from environment variable."""
        # Set a test API key
        test_api_key = "test-api-key-from-env"
        os.environ["NEBIUS_API_KEY"] = test_api_key
        
        # Create predictor without providing api_key parameter
        predictor = CommoditySentimentPredictor()
        
        # Check that the API key was correctly retrieved
        self.assertEqual(predictor.api_key, test_api_key)

    def test_api_key_parameter_takes_precedence(self):
        """Test that provided api_key parameter takes precedence over environment variable."""
        # Set a test API key in environment
        env_api_key = "env-api-key"
        os.environ["NEBIUS_API_KEY"] = env_api_key
        
        # Create predictor with a different api_key parameter
        param_api_key = "param-api-key"
        predictor = CommoditySentimentPredictor(api_key=param_api_key)
        
        # Check that the parameter API key was used
        self.assertEqual(predictor.api_key, param_api_key)

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises appropriate error."""
        # Ensure no API key is set
        if "NEBIUS_API_KEY" in os.environ:
            del os.environ["NEBIUS_API_KEY"]
        
        # Check that creating predictor raises ValueError
        with self.assertRaises(ValueError) as context:
            CommoditySentimentPredictor()
        
        # Check that the error message is informative
        self.assertIn("NEBIUS_API_KEY environment variable not set", str(context.exception))
        self.assertIn("Please set the NEBIUS_API_KEY environment variable", str(context.exception))

    def test_empty_api_key_raises_error(self):
        """Test that empty API key raises appropriate error."""
        # Set empty API key
        os.environ["NEBIUS_API_KEY"] = ""
        
        # Check that creating predictor raises ValueError
        with self.assertRaises(ValueError) as context:
            CommoditySentimentPredictor()
        
        # Check that the error message is informative
        self.assertIn("NEBIUS_API_KEY is empty or contains only whitespace", str(context.exception))

    def test_whitespace_only_api_key_raises_error(self):
        """Test that whitespace-only API key raises appropriate error."""
        # Set whitespace-only API key
        os.environ["NEBIUS_API_KEY"] = "   \n\t  "
        
        # Check that creating predictor raises ValueError
        with self.assertRaises(ValueError) as context:
            CommoditySentimentPredictor()
        
        # Check that the error message is informative
        self.assertIn("NEBIUS_API_KEY is empty or contains only whitespace", str(context.exception))

    def test_valid_api_key_with_whitespace(self):
        """Test that valid API key with surrounding whitespace is trimmed."""
        # Set API key with surrounding whitespace
        test_api_key = "  valid-api-key-with-whitespace  "
        os.environ["NEBIUS_API_KEY"] = test_api_key
        
        # Create predictor
        predictor = CommoditySentimentPredictor()
        
        # Check that the API key was trimmed
        self.assertEqual(predictor.api_key, test_api_key.strip())

    def test_api_key_is_stored_correctly(self):
        """Test that the API key is stored correctly in the predictor instance."""
        # Set a test API key
        test_api_key = "test-api-key-storage"
        os.environ["NEBIUS_API_KEY"] = test_api_key
        
        # Create predictor
        predictor = CommoditySentimentPredictor()
        
        # Check that the API key is stored correctly
        self.assertEqual(predictor.api_key, test_api_key)
        
        # Check that the client property uses the API key
        # We can't test the actual client initialization without a valid API key,
        # but we can check that the API key is passed correctly
        with patch('predictor.OpenAI') as mock_openai:
            _ = predictor.client
            mock_openai.assert_called_once_with(
                base_url="https://api.studio.nebius.com/v1/",
                api_key=test_api_key
            )


def run_tests():
    """Run all tests and print results."""
    print("Running NEBIUS_API_KEY retrieval tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNebiusAPIKeyRetrieval)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 50)
    if result.wasSuccessful():
        print("All tests passed! ✓")
        return 0
    else:
        print(f"Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
#!/usr/bin/env python3
"""
Test script for the commodity signal system
Tests core functionality of the sugar news processing pipeline
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir / "ShinkaEvolve"
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
        from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline
        from sugar.backend.parsers.news_parser import clean_html, contains_keywords
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_triage_filter():
    """Test the triage filter functionality"""
    print("\nTesting triage filter...")
    
    try:
        from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
        
        # Test cases
        test_cases = [
            {
                "text": "Brazilian sugar exports are rising due to market price changes.",
                "expected": True,
                "description": "Valid sugar news with market context"
            },
            {
                "text": "Copper prices are rising in the commodity market.",
                "expected": False,
                "description": "Non-sugar commodity news"
            },
            {
                "text": "Sugar production in Brazil affected by drought conditions.",
                "expected": True,
                "description": "Sugar news with weather event"
            },
            {
                "text": "Generic market news about inflation and interest rates.",
                "expected": False,
                "description": "Generic market news without sugar context"
            }
        ]
        
        passed = 0
        for i, test_case in enumerate(test_cases):
            result = triage_filter(test_case["text"])
            if result["passed"] == test_case["expected"]:

#!/usr/bin/env python3
"""
Simple test to verify the German compound word fix.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import generate_content_hash

def test_german_fix():
    """Test the German compound word fix"""
    
    # Test text with German compound words
    test_text = "Der Zuckerpreis steigt stark an. Die Zuckerproduktion in Deutschland ist wichtig. Auch Zuckerrüben und Zuckersirup werden produziert."
    
    print("Original text:", test_text)
    
    # Generate hash with keywords
    hash_with_keywords = generate_content_hash(test_text, test_text, "test_source")
    print("Hash with keywords:", hash_with_keywords)
    
    # Create text without keywords
    text_without_keywords = test_text.replace("Zucker", "").replace("zucker", "").replace("Zuckerrüben", "").replace("zuckerrüben", "").replace("Zuckersirup", "").replace("zuckersirup", "")
    print("Text without keywords:", text_without_keywords)
    
    # Generate hash without keywords
    hash_without_keywords = generate_content_hash(text_without_keywords, text_without_keywords, "test_source")
    print("Hash without keywords:", hash_without_keywords)
    
    print("Hashes are different:", hash_with_keywords != hash_without_keywords)
    
    if hash_with_keywords != hash_without_keywords:
        print("✓ PASS: German compound words are preserved correctly")
    else:
        print("✗ FAIL: German compound words are not preserved")

if __name__ == "__main__":
    test_german_fix()
#!/usr/bin/env python3
"""
Debug script to understand why German compound words are not being preserved.
"""

import sys
import os
import re
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import generate_content_hash

def debug_german_compound():
    """Debug German compound word processing"""
    
    # Test text with German compound words
    test_text = "Der Zuckerpreis steigt stark an. Die Zuckerproduktion in Deutschland ist wichtig. Auch Zuckerrüben und Zuckersirup werden produziert."
    
    print("Original text:", test_text)
    
    # Generate hash with keywords
    hash_with_keywords = generate_content_hash(test_text, test_text, "test_source")
    print("Hash with keywords:", hash_with_keywords)
    
    # Create text without keywords
    text_without_keywords = test_text.replace("Zucker", "").replace("zucker", "")
    print("Text without keywords:", text_without_keywords)
    
    # Generate hash without keywords
    hash_without_keywords = generate_content_hash(text_without_keywords, text_without_keywords, "test_source")
    print("Hash without keywords:", hash_without_keywords)
    
    print("Hashes are different:", hash_with_keywords != hash_without_keywords)
    
    # Let's also test the normalize_content function directly
    print("\n=== Testing normalize_content directly ===")
    
    # Import the normalize_content function by extracting it
    import re
    import hashlib
    
    def normalize_content(content):
        if not content:
            return ""
        
        # CRITICAL FIX: Preserve multilingual sugar keywords before any processing
        # Create a pattern to match all multilingual sugar keywords
        multilingual_sugar_keywords = [
            # European languages
            "sucre", "azúcar", "zucchero", "açúcar", "zucker", "sukker", "soker", "cukor",
            "cukier", "cukr", "sahara", "ζάχαρη", "cukor", "soker", "sugar", "sukker",
            # Asian languages
            "शक्कर", "चीनी", "চিনি", "சர்க்கரை", "చక్కరో", "ಸಕ್ಕರೆ", "പഞ്ചശര", "සීනි",
            "شکر", "سكر", "शक्कर", "चीनी", "gula", "gularen", "gula aren", "gula merah",
            "น้ำตาล", "น้ำตาลทราย", "อ้อย", "ตะกั่ว", "茶糖", "砂糖", "糖", "설탕", "설탕물",
            # Other major languages
            "şeker", "şekerli", "cukier", "cukrowy", "сахар", "сахарный", "цукор", "цукровий",
            "mishukozi", "asali", "sukari", "chini", "tumbura", "sukali", "sukari", "shakar",
            "shakkar", "misri", "khanda", "gud", "jaggery", "panela", "piloncillo", "rapadura"
        ]
        
        # CRITICAL FIX: Handle German compound words by using a simpler, more direct approach
        # We need to match both exact keywords and keywords that are part of compound words
        # This handles cases like "Zuckerpreis" where "Zucker" is part of the compound word
        
        # First, let's handle German compound words with a special approach
        # We'll look for German sugar keywords within compound words and extract them
        german_compound_keywords = ["zucker", "zuckerrübe", "zuckersirup"]
        
        # Create a map to store all the matches and their placeholders
        keyword_map = {}
        placeholder_count = 0
        
        print("Original content:", repr(content))
        
        # Process German compound words first
        for keyword in german_compound_keywords:
            print(f"Processing keyword: {keyword}")
            # Find all occurrences of the keyword, including within compound words
            # We'll use a case-insensitive search
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = list(pattern.finditer(content))
            print(f"Found {len(matches)} matches for {keyword}")
            
            for match in matches:
                matched_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                print(f"  Match: {matched_text} at position {start_pos}-{end_pos}")
                
                # Check if this is part of a compound word
                is_compound = False
                
                # Check if it's at the beginning of a compound word (followed by uppercase)
                if end_pos < len(content) and content[end_pos].isupper():
                    is_compound = True
                    print(f"  Followed by uppercase: {content[end_pos]}")
                
                # Check if it's in the middle of a compound word (preceded by lowercase)
                if start_pos > 0 and content[start_pos-1].islower():
                    is_compound = True
                    print(f"  Preceded by lowercase: {content[start_pos-1]}")
                
                # For compound words, we want to preserve the entire compound word
                if is_compound:
                    # Extract the full compound word
                    word_start = start_pos
                    word_end = end_pos
                    
                    # Extend to the beginning of the word
                    while word_start > 0 and content[word_start-1].isalpha():
                        word_start -= 1
                    
                    # Extend to the end of the word
                    while word_end < len(content) and content[word_end].isalpha():
                        word_end += 1
                    
                    compound_word = content[word_start:word_end]
                    print(f"  Compound word: {compound_word}")
                    
                    placeholder = f"__GERMAN_COMPOUND_SUGAR_{placeholder_count}__"
                    keyword_map[placeholder] = compound_word
                    content = content.replace(compound_word, placeholder)
                    placeholder_count += 1
                else:
                    # For standalone keywords, use the original approach
                    placeholder = f"__STANDALONE_SUGAR_{placeholder_count}__"
                    keyword_map[placeholder] = matched_text
                    content = content.replace(matched_text, placeholder, 1)  # Replace only this occurrence
                    placeholder_count += 1
        
        print("Content after German processing:", repr(content))
        print("Keyword map:", keyword_map)
        
        # Now handle other multilingual keywords with the original approach
        other_keywords = [k for k in multilingual_sugar_keywords if k not in german_compound_keywords]
        if other_keywords:
            other_pattern = '\\b(' + '|'.join(re.escape(keyword) for keyword in other_keywords) + ')\\b'
            other_matches = list(re.finditer(other_pattern, content, re.IGNORECASE))
            
            for match in other_matches:
                matched_text = match.group(0)
                placeholder = f"__OTHER_SUGAR_{placeholder_count}__"
                keyword_map[placeholder] = matched_text
                content = content.replace(matched_text, placeholder, 1)  # Replace only this occurrence
                placeholder_count += 1
        
        print("Content after all processing:", repr(content))
        
        # Convert to lowercase
        content = content.lower()
        print("Content after lowercase:", repr(content))
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove URLs, email addresses, and other non-content elements
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        content = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', content)
        
        # Remove punctuation but preserve word boundaries
        # Use a more inclusive pattern that preserves non-Latin characters
        content = re.sub(r'[^\w\s\u0900-\u097F\u0B80-\u0BFF\u0E00-\u0E7F\uAC00-\uD7AF\u3040-\u309F\u30A0-\u30FF\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF]', ' ', content)
        
        print("Content after punctuation removal:", repr(content))
        
        # Restore multilingual sugar keywords from placeholders
        for placeholder, original_text in keyword_map.items():
            # For German compound words, we want to preserve the original case and extract the keyword
            if placeholder.startswith('__GERMAN_COMPOUND_SUGAR_'):
                # Extract the German keyword from the compound word
                for keyword in german_compound_keywords:
                    if keyword.lower() in original_text.lower():
                        # Add the extracted keyword in lowercase
                        print(f"Restoring German compound {placeholder} -> {keyword.lower()}")
                        content = content.replace(placeholder.lower(), keyword.lower())
                        break
                else:
                    # If no keyword found, just use the original text in lowercase
                    print(f"Restoring German compound {placeholder} -> {original_text.lower()}")
                    content = content.replace(placeholder.lower(), original_text.lower())
            else:
                # For other keywords, use the original text in lowercase
                print(f"Restoring other {placeholder} -> {original_text.lower()}")
                content = content.replace(placeholder.lower(), original_text.lower())
        
        print("Final content:", repr(content))
        
        # Normalize common variations
        # CRITICAL FIX: Preserve important sugar keywords for triage filter
        # Only normalize generic "sugar" references, but preserve specific sugar terms
        # that are important for the triage filter to detect sugar-related content
        content = re.sub(r'\bsugar\b(?!\s*(cane|beet))', 'sugar', content)  # Only normalize standalone "sugar"
        # DO NOT normalize: sugarcane, sugar beet, whites, NY11, LSU, LON No. 5, etc.
        content = re.sub(r'\b(price|prices|pricing|cost|costs)\b', 'price', content)  # Normalize price terms
        content = re.sub(r'\b(rise|rise|rising|increase|increased|up|higher)\b', 'rise', content)  # Normalize upward movement
        content = re.sub(r'\b(fall|fell|falling|decrease|decreased|down|lower)\b', 'fall', content)  # Normalize downward movement
        content = re.sub(r'\b(market|markets)\b', 'market', content)  # Normalize market terms
        content = re.sub(r'\b(supply|supplies)\b', 'supply', content)  # Normalize supply terms
        content = re.sub(r'\b(demand|demands)\b', 'demand', content)  # Normalize demand terms
        
        # Remove common stop words that don't affect meaning
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        words = content.split()
        words = [word for word in words if word not in stop_words]
        content = ' '.join(words)
        
        # Strip leading/trailing whitespace
        content = content.strip()
        
        return content
    
    # Test the normalize_content function
    normalized = normalize_content(test_text)
    print("\nNormalized text:", normalized)
    
    # Check if "zucker" is in the normalized text
    print("Contains 'zucker':", 'zucker' in normalized)

if __name__ == "__main__":
    debug_german_compound()
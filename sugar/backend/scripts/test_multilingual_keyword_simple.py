#!/usr/bin/env python3
"""
Simple test script to verify that multilingual sugar keywords are preserved during normalization.

This script directly imports and uses the normalize_content function from sugar_news_fetcher.py
to ensure that multilingual sugar keywords are not normalized and are preserved correctly.
"""

import sys
import os
import re
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the generate_content_hash function which contains normalize_content
from sugar.backend.parsers.sugar_news_fetcher import generate_content_hash

def extract_normalize_content_function():
    """
    Extract the normalize_content function from generate_content_hash.
    """
    import inspect
    
    # Get the source code of the generate_content_hash function
    source = inspect.getsource(generate_content_hash)
    
    # Find the start of the normalize_content function
    start_idx = source.find('def normalize_content(content):')
    if start_idx == -1:
        raise ValueError("Could not find normalize_content function in generate_content_hash")
    
    # Extract just the normalize_content function
    lines = source[start_idx:].split('\n')
    normalize_lines = []
    indent_level = None
    
    for line in lines:
        if line.startswith('def ') and line != 'def normalize_content(content):':
            # Found the next function, stop
            break
        if line.strip() == '':
            # Empty line, add it
            normalize_lines.append(line)
        elif line.startswith('def normalize_content(content):'):
            # First line of the function
            normalize_lines.append(line)
            indent_level = len(line) - len(line.lstrip())
        elif line.startswith(' ') and indent_level is not None:
            # Inside the function
            current_indent = len(line) - len(line.lstrip())
            if current_indent > indent_level:
                normalize_lines.append(line)
            else:
                # Function ended
                break
        else:
            # Function ended
            break
    
    # Join the lines to get the function definition
    normalize_func_def = '\n'.join(normalize_lines)
    
    # Execute the function definition to make it available
    exec(normalize_func_def)
    
    return locals()['normalize_content']

def test_multilingual_keyword_preservation():
    """
    Test that multilingual sugar keywords are preserved during normalization.
    """
    print("Testing multilingual sugar keyword preservation...")
    
    # Get the normalize_content function
    normalize_content = extract_normalize_content_function()
    
    # Define test cases with multilingual sugar keywords
    test_cases = [
        # European languages
        {
            'title': 'French sugar article',
            'text': 'Le prix du sucre a augmenté. La production de sucre est en hausse.',
            'expected_keywords': ['sucre']
        },
        {
            'title': 'Spanish sugar article',
            'text': 'El precio del azúcar ha subido. La producción de azúcar está en aumento.',
            'expected_keywords': ['azúcar']
        },
        {
            'title': 'Italian sugar article',
            'text': 'Il prezzo dello zucchero è aumentato. La produzione di zucchero è in aumento.',
            'expected_keywords': ['zucchero']
        },
        {
            'title': 'Portuguese sugar article',
            'text': 'O preço do açúcar aumentou. A produção de açúcar está em alta.',
            'expected_keywords': ['açúcar']
        },
        {
            'title': 'German sugar article',
            'text': 'Der Zuckerpreis ist gestiegen. Die Zuckerproduktion steigt.',
            'expected_keywords': ['zucker']
        },
        {
            'title': 'Polish sugar article',
            'text': 'Cena cukru wzrosła. Produkcja cukru rośnie.',
            'expected_keywords': ['cukru', 'cukru']
        },
        {
            'title': 'Russian sugar article',
            'text': 'Цена на сахар выросла. Производство сахара растет.',
            'expected_keywords': ['сахар']
        },
        {
            'title': 'Turkish sugar article',
            'text': 'Şeker fiyatı arttı. Şeker üretimi artıyor.',
            'expected_keywords': ['şeker']
        },
        
        # Asian languages
        {
            'title': 'Hindi sugar article',
            'text': 'चीनी की कीमत बढ़ गई है। चीनी का उत्पादन बढ़ रहा है।',
            'expected_keywords': ['चीनी', 'चीनी']
        },
        {
            'title': 'Bengali sugar article',
            'text': 'চিনির দাম বেড়েছে। চিনি উৎপাদন বাড়ছে।',
            'expected_keywords': ['চিনি', 'চিনি']
        },
        {
            'title': 'Thai sugar article',
            'text': 'ราคาน้ำตาลเพิ่มขึ้น การผลิตน้ำตาลเพิ่มขึ้น',
            'expected_keywords': ['น้ำตาล', 'น้ำตาล']
        },
        {
            'title': 'Indonesian sugar article',
            'text': 'Harga gula naik. Produksi gula meningkat.',
            'expected_keywords': ['gula', 'gula']
        },
        {
            'title': 'Japanese sugar article',
            'text': '砂糖の価格が上昇しました。砂糖の生産が増加しています。',
            'expected_keywords': ['砂糖', '砂糖']
        },
        {
            'title': 'Korean sugar article',
            'text': '설탕 가격이 올랐습니다. 설탕 생산이 증가하고 있습니다.',
            'expected_keywords': ['설탕', '설탕']
        },
        
        # Other major languages
        {
            'title': 'Swahili sugar article',
            'text': 'Bei ya sukari imepanda. Uzalishaji wa sukari unaoongezeka.',
            'expected_keywords': ['sukari', 'sukari']
        },
        {
            'title': 'Arabic sugar article',
            'text': 'ارتفع سعر السكر. إنتاج السكر في ازدياد.',
            'expected_keywords': ['السكر', 'السكر']
        },
        {
            'title': 'Hausa sugar article',
            'text': 'Farashin sukari ta tashi. Samar sukari tana ƙaruwa.',
            'expected_keywords': ['sukari', 'sukari']
        },
        
        # Mixed content with punctuation
        {
            'title': 'Mixed content with punctuation',
            'text': 'Le sucre, le azúcar, and the zucchero! All types of sugar... including açúcar, Zucker, and चीनी?',
            'expected_keywords': ['sucre', 'azúcar', 'zucchero', 'açúcar', 'zucker', 'चीनी']
        },
        
        # Edge case: keywords with numbers and special characters
        {
            'title': 'Keywords with special context',
            'text': 'O preço do açúcar (gula aren) aumentou 10%. O gula merah também subiu.',
            'expected_keywords': ['açúcar', 'gula', 'aren', 'gula', 'merah']
        }
    ]
    
    # Test each case
    passed_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case['title']}")
        print(f"Original text: {test_case['text']}")
        
        # Normalize the text using the actual normalize_content function
        normalized_text = normalize_content(test_case['text'])
        print(f"Normalized text: {normalized_text}")
        
        # Check if expected keywords are preserved
        all_keywords_preserved = True
        missing_keywords = []
        
        for keyword in test_case['expected_keywords']:
            if keyword.lower() not in normalized_text.lower():
                all_keywords_preserved = False
                missing_keywords.append(keyword)
        
        if all_keywords_preserved:
            print(f"✓ PASS: All expected keywords preserved: {test_case['expected_keywords']}")
            passed_tests += 1
        else:
            print(f"✗ FAIL: Missing keywords: {missing_keywords}")
            failed_tests += 1
    
    # Print summary
    print(f"\n=== TEST SUMMARY ===")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("✓ All tests passed! Multilingual sugar keywords are preserved correctly.")
        return True
    else:
        print("✗ Some tests failed. Multilingual sugar keywords preservation needs attention.")
        return False

def test_english_keyword_preservation():
    """
    Test that English sugar keywords are still preserved during normalization.
    """
    print("\nTesting English sugar keyword preservation...")
    
    # Get the normalize_content function
    normalize_content = extract_normalize_content_function()
    
    # Define test cases with English sugar keywords
    test_cases = [
        {
            'title': 'Basic sugar keywords',
            'text': 'Sugar prices are rising. Sugar production is increasing.',
            'expected_keywords': ['sugar', 'sugar']
        },
        {
            'title': 'Sugar cane and sugar beet',
            'text': 'Sugar cane and sugar beet production are both important.',
            'expected_keywords': ['sugar', 'cane', 'sugar', 'beet']
        },
        {
            'title': 'Sugar futures',
            'text': 'Sugar futures trading is active. NY11 sugar prices are volatile.',
            'expected_keywords': ['sugar', 'ny11', 'sugar']
        },
        {
            'title': 'Sugar with punctuation',
            'text': 'Sugar, sugar! What about sugar? All types of sugar...',
            'expected_keywords': ['sugar', 'sugar', 'sugar', 'sugar']
        }
    ]
    
    # Test each case
    passed_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case['title']}")
        print(f"Original text: {test_case['text']}")
        
        # Normalize the text
        normalized_text = normalize_content(test_case['text'])
        print(f"Normalized text: {normalized_text}")
        
        # Check if expected keywords are preserved
        all_keywords_preserved = True
        missing_keywords = []
        
        for keyword in test_case['expected_keywords']:
            if keyword.lower() not in normalized_text.lower():
                all_keywords_preserved = False
                missing_keywords.append(keyword)
        
        if all_keywords_preserved:
            print(f"✓ PASS: All expected keywords preserved: {test_case['expected_keywords']}")
            passed_tests += 1
        else:
            print(f"✗ FAIL: Missing keywords: {missing_keywords}")
            failed_tests += 1
    
    # Print summary
    print(f"\n=== ENGLISH KEYWORD TEST SUMMARY ===")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("✓ All tests passed! English sugar keywords are preserved correctly.")
        return True
    else:
        print("✗ Some tests failed. English sugar keywords preservation needs attention.")
        return False

def main():
    """
    Main function to run all tests.
    """
    print("=== MULTILINGUAL SUGAR KEYWORD PRESERVATION TEST ===")
    
    # Test multilingual keyword preservation
    multilingual_result = test_multilingual_keyword_preservation()
    
    # Test English keyword preservation
    english_result = test_english_keyword_preservation()
    
    # Overall result
    print(f"\n=== OVERALL TEST RESULT ===")
    if multilingual_result and english_result:
        print("✓ ALL TESTS PASSED! Both multilingual and English sugar keywords are preserved correctly.")
        return 0
    else:
        print("✗ SOME TESTS FAILED! Keyword preservation needs attention.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
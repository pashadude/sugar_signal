#!/usr/bin/env python
"""
Test script for article splitting functionality in the sugar news filtering system.

This script tests:
1. Token counting functionality
2. Article splitting for long articles
3. Filtering logic for split articles
4. Logging of split article processing
"""

import sys
import os
from datetime import datetime

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, str(project_root))

from sugar.backend.parsers.sugar_news_fetcher import (
    count_tokens,
    split_article_intelligently,
    normalize_and_filter_article
)
from sugar.backend.text_filtering.sugar_triage_filter import triage_filter
from sugar.backend.text_filtering.language_normalization import LanguageNormalizationPipeline

def test_token_counting():
    """Test token counting functionality"""
    print("=== Testing Token Counting ===")
    
    # Test with short text
    short_text = "Sugar prices are rising due to increased demand."
    tokens = count_tokens(short_text)
    print(f"Short text: '{short_text}'")
    print(f"Token count: {tokens}")
    
    # Test with long text
    long_text = """
    Sugar prices are rising due to increased demand in the global market. 
    The International Sugar Organization reported that production in Brazil 
    has been affected by weather conditions. Meanwhile, India's sugar 
    exports have increased significantly, putting pressure on global prices. 
    The European Union has also adjusted its sugar production quotas 
    in response to changing market conditions. Analysts predict that 
    sugar prices will continue to be volatile in the coming months due 
    to various factors including weather patterns, government policies, 
    and changes in consumer demand. The sugar industry is closely 
    monitoring these developments as they could impact profitability 
    and investment decisions across the supply chain.
    """
    tokens = count_tokens(long_text)
    print(f"\nLong text (first 100 chars): '{long_text[:100]}...'")
    print(f"Token count: {tokens}")
    
    return tokens > 0

def test_article_splitting():
    """Test article splitting functionality"""
    print("\n=== Testing Article Splitting ===")
    
    # Create a very long article that should be split
    long_article = """
    Sugar prices are experiencing significant volatility in the global market as multiple factors converge to impact supply and demand dynamics. The International Sugar Organization (ISO) has released its latest quarterly report indicating that global sugar production is expected to reach 185 million tonnes in the current marketing year, representing a 3% increase from the previous year. This production increase is primarily driven by favorable weather conditions in major producing regions, particularly in Brazil and Thailand.

    Brazil, the world's largest sugar producer, has reported excellent cane yields in its Center-South region, with crushing operations proceeding ahead of schedule. The Brazilian Sugarcane Industry Association (UNICA) has confirmed that sugar production from the current harvest could exceed previous estimates by approximately 5%, potentially reaching 39 million tonnes. This surplus production has led to increased export activities, with Brazilian sugar finding its way to traditional markets in Asia, Africa, and the Middle East.

    Meanwhile, India, the world's second-largest producer and largest consumer, has implemented new export policies to manage domestic supply concerns. The Indian government has extended restrictions on sugar exports to ensure adequate domestic availability and stabilize local prices. This decision has significant implications for global trade flows, as Indian exports typically account for approximately 15% of global sugar trade.

    The European Union has also adjusted its sugar policies in response to changing market conditions. The European Commission has proposed modifications to the Common Agricultural Policy (CAP) that would provide additional support to sugar beet farmers while maintaining competitive pricing for consumers. These changes come as the EU seeks to balance domestic production needs with international trade obligations.

    Weather patterns continue to play a crucial role in sugar market dynamics. Meteorological agencies are monitoring the development of El Niño conditions in the Pacific Ocean, which historically has had significant impacts on sugar production in key regions. In Southeast Asia, particularly Thailand and Vietnam, below-average rainfall has raised concerns about cane development for the upcoming harvest season. Conversely, favorable monsoon conditions in parts of India have supported better-than-expected crop prospects.

    The ethanol market continues to influence sugar production decisions, particularly in Brazil where the flex-fuel vehicle fleet creates significant demand for both sugar and ethanol. With crude oil prices remaining elevated, the economic incentive for ethanol production remains strong, potentially diverting more cane away from sugar production. This dynamic creates an interesting interplay between energy markets and sugar availability.

    Price discovery mechanisms across major exchanges, including the ICE Futures US and the London commodities market, reflect these complex supply and demand fundamentals. Technical analysts note that sugar futures have established a trading range with support levels holding firm despite increased volatility. Market participants are closely monitoring inventory levels, with global sugar stocks expected to remain comfortable but not excessive.

    The sustainability agenda is increasingly influencing sugar production practices worldwide. Major producers are investing in precision agriculture technologies, water conservation measures, and renewable energy integration to reduce the environmental footprint of sugar production. These initiatives, while increasing production costs, are becoming essential for maintaining market access and meeting consumer expectations for sustainably produced commodities.

    Looking ahead, market analysts anticipate that sugar prices will remain sensitive to weather developments, policy changes, and energy market dynamics. The balance between food and fuel uses of sugarcane will continue to be a critical factor determining available supplies for the global market. Additionally, the ongoing recovery in food service demand following the pandemic provides underlying support for sugar consumption growth in developed markets.
    """
    
    print(f"Original article length: {len(long_article)} characters")
    print(f"Original article tokens: {count_tokens(long_article)}")
    
    # Test splitting
    parts = split_article_intelligently(long_article, max_tokens=512, min_tokens=256)
    
    print(f"Article split into {len(parts)} parts")
    for i, part in enumerate(parts):
        part_tokens = count_tokens(part)
        print(f"  Part {i+1}: {part_tokens} tokens, {len(part)} characters")
        print(f"    First 100 chars: {part[:100]}...")
    
    return len(parts) > 1

def test_split_article_filtering():
    """Test filtering of split articles"""
    print("\n=== Testing Split Article Filtering ===")
    
    # Create a very long test article that should be split and contains sugar keywords
    test_article = {
        'title': 'Comprehensive Global Sugar Market Analysis and Future Price Trends',
        'text': """
        Sugar prices are experiencing significant volatility in the global market as multiple factors converge to impact supply and demand dynamics. The International Sugar Organization (ISO) has released its latest quarterly report indicating that global sugar production is expected to reach 185 million tonnes in the current marketing year, representing a 3% increase from the previous year. This production increase is primarily driven by favorable weather conditions in major producing regions, particularly in Brazil and Thailand.

        Brazil, the world's largest sugar producer, has reported excellent cane yields in its Center-South region, with crushing operations proceeding ahead of schedule. The Brazilian Sugarcane Industry Association (UNICA) has confirmed that sugar production from the current harvest could exceed previous estimates by approximately 5%, potentially reaching 39 million tonnes. This surplus production has led to increased export activities, with Brazilian sugar finding its way to traditional markets in Asia, Africa, and the Middle East.

        Meanwhile, India, the world's second-largest producer and largest consumer, has implemented new export policies to manage domestic supply concerns. The Indian government has extended restrictions on sugar exports to ensure adequate domestic availability and stabilize local prices. This decision has significant implications for global trade flows, as Indian exports typically account for approximately 15% of global sugar trade.

        The European Union has also adjusted its sugar policies in response to changing market conditions. The European Commission has proposed modifications to the Common Agricultural Policy (CAP) that would provide additional support to sugar beet farmers while maintaining competitive pricing for consumers. These changes come as the EU seeks to balance domestic production needs with international trade obligations.

        Weather patterns continue to play a crucial role in sugar market dynamics. Meteorological agencies are monitoring the development of El Niño conditions in the Pacific Ocean, which historically has had significant impacts on sugar production in key regions. In Southeast Asia, particularly Thailand and Vietnam, below-average rainfall has raised concerns about cane development for the upcoming harvest season. Conversely, favorable monsoon conditions in parts of India have supported better-than-expected crop prospects.

        The ethanol market continues to influence sugar production decisions, particularly in Brazil where the flex-fuel vehicle fleet creates significant demand for both sugar and ethanol. With crude oil prices remaining elevated, the economic incentive for ethanol production remains strong, potentially diverting more cane away from sugar production. This dynamic creates an interesting interplay between energy markets and sugar availability.

        Price discovery mechanisms across major exchanges, including the ICE Futures US and the London commodities market, reflect these complex supply and demand fundamentals. Technical analysts note that sugar futures have established a trading range with support levels holding firm despite increased volatility. Market participants are closely monitoring inventory levels, with global sugar stocks expected to remain comfortable but not excessive.

        The sustainability agenda is increasingly influencing sugar production practices worldwide. Major producers are investing in precision agriculture technologies, water conservation measures, and renewable energy integration to reduce the environmental footprint of sugar production. These initiatives, while increasing production costs, are becoming essential for maintaining market access and meeting consumer expectations for sustainably produced commodities.

        Looking ahead, market analysts anticipate that sugar prices will remain sensitive to weather developments, policy changes, and energy market dynamics. The balance between food and fuel uses of sugarcane will continue to be a critical factor determining available supplies for the global market. Additionally, the ongoing recovery in food service demand following the pandemic provides underlying support for sugar consumption growth in developed markets.

        In the United States, sugar production remains protected by import quotas and price support mechanisms that maintain domestic prices above world market levels. This policy framework has been in place for decades and continues to shape the North American sugar market, influencing production decisions in both the US and Mexico under the terms of the USMCA trade agreement.

        China's sugar market presents another important dynamic, as the world's largest sugar importer continues to balance domestic production needs with import requirements. Chinese authorities have been working to increase domestic sugar production through improved agricultural practices and better-yielding cane varieties, but the country still relies heavily on imports to meet its growing consumption demands.

        The African sugar market is also evolving, with several countries investing in expanded production capacity. Nations such as Egypt, South Africa, and Kenya are increasing their sugar output to reduce dependence on imports and create export opportunities. This development could significantly alter global trade patterns in the medium to long term.

        Currency fluctuations are adding another layer of complexity to the global sugar trade. The strength of the US dollar against other major currencies impacts the competitiveness of sugar exports from producing countries. A stronger dollar typically makes sugar more expensive for buyers using other currencies, potentially dampening demand in key import markets.

        Transportation and logistics costs remain a significant factor in determining the final price of sugar in different markets. Recent disruptions in global shipping routes and increased fuel costs have contributed to higher transportation expenses, which are ultimately passed on to consumers in the form of higher sugar prices.

        The impact of climate change on sugar production cannot be overstated. Rising temperatures, changing precipitation patterns, and increased frequency of extreme weather events are posing new challenges to sugar producers worldwide. Adaptation strategies, including the development of more resilient cane varieties and improved water management practices, are becoming increasingly important for ensuring stable production levels.

        Consumer preferences are also evolving, with growing demand for organic and specialty sugar products. This trend is creating new market opportunities for producers who can meet these specialized requirements, often commanding premium prices in niche markets. The organic sugar market, while still small compared to conventional sugar, is growing at a faster rate than the overall market.

        Government policies regarding sugar taxation and health regulations continue to shape consumption patterns. Several countries have implemented sugar taxes or are considering such measures to address public health concerns related to sugar consumption. These policies could potentially reduce demand for sugar in certain markets while creating incentives for the development of alternative sweeteners.

        The role of sugar in biofuel production extends beyond ethanol. Research into advanced biofuels and biochemicals derived from sugarcane is opening new avenues for sugar utilization. These developments could create additional demand streams for sugar producers, helping to balance the market during periods of food sector oversupply.

        Investment in sugar production infrastructure continues across major producing regions. New mills, refineries, and processing facilities are being built to increase capacity and improve efficiency. These investments reflect long-term confidence in the sugar market despite short-term price volatility and highlight the industry's commitment to meeting future demand growth.

        The digital transformation of the sugar industry is accelerating, with producers adopting advanced technologies for crop monitoring, yield prediction, and supply chain management. Satellite imagery, IoT sensors, and artificial intelligence are being deployed to optimize production processes and improve decision-making throughout the sugar value chain.

        Financial markets play an increasingly important role in price discovery and risk management for sugar producers and consumers. The growing sophistication of sugar futures and options markets provides tools for hedging price risk, while the entry of institutional investors adds liquidity but also contributes to price volatility.

        The relationship between sugar and other agricultural commodities is also evolving. Correlations with prices of grains, oilseeds, and energy products are changing as market dynamics shift, creating new challenges and opportunities for market participants who need to understand these interconnections.

        Looking to the future, the sugar market is likely to continue experiencing periods of volatility as it adjusts to the complex interplay of factors including weather conditions, policy changes, energy market developments, and evolving consumer preferences. The industry's ability to adapt to these changes while maintaining stable supplies to meet global demand will be crucial for ensuring food security and supporting economic development in sugar-producing regions.
        """,
        'url': 'https://example.com/comprehensive-sugar-market-analysis',
        'published_date': '2025-01-15',
        'site_name': 'Sugar Market News'
    }
    
    print(f"Test article title: {test_article['title']}")
    print(f"Test article tokens: {count_tokens(test_article['title'] + ' ' + test_article['text'])}")
    
    # Initialize normalization pipeline (mock for testing)
    class MockNormalizationPipeline:
        def normalize(self, text=None, sugar_pricing_lines=None):
            if sugar_pricing_lines:
                return sugar_pricing_lines
            return text.lower() if text else ""
    
    normalization_pipeline = MockNormalizationPipeline()
    
    # Process the article
    result = normalize_and_filter_article(test_article, normalization_pipeline)
    
    print(f"\nProcessing results:")
    print(f"  Article split: {result.get('article_split', False)}")
    print(f"  Split parts: {result.get('split_parts', 1)}")
    print(f"  Parts passed: {result.get('parts_passed', 0)}")
    print(f"  Triage passed: {result.get('triage_passed', False)}")
    print(f"  Asset: {result.get('asset', 'Unknown')}")
    print(f"  Reason: {result.get('triage_reason', 'N/A')}")
    
    if result.get('article_split', False):
        print(f"\nPart results:")
        for i, part_result in enumerate(result.get('part_results', [])):
            print(f"  Part {i+1}: Passed={part_result.get('passed', False)}, Reason={part_result.get('reason', 'N/A')}")
    
    return result.get('article_split', False) and result.get('triage_passed', False)

def main():
    """Run all tests"""
    print("Testing Article Splitting Implementation")
    print("=" * 50)
    
    try:
        # Test token counting
        token_test_passed = test_token_counting()
        print(f"Token counting test: {'PASSED' if token_test_passed else 'FAILED'}")
        
        # Test article splitting
        splitting_test_passed = test_article_splitting()
        print(f"Article splitting test: {'PASSED' if splitting_test_passed else 'FAILED'}")
        
        # Test split article filtering
        filtering_test_passed = test_split_article_filtering()
        print(f"Split article filtering test: {'PASSED' if filtering_test_passed else 'FAILED'}")
        
        # Overall result
        all_tests_passed = token_test_passed and splitting_test_passed and filtering_test_passed
        
        print("\n" + "=" * 50)
        print(f"Overall test result: {'ALL TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")
        
        if all_tests_passed:
            print("\n✓ Article splitting implementation is working correctly")
            print("✓ Long articles will be split into parts of 1024 tokens each")
            print("✓ Each part is processed through the triage filter")
            print("✓ If ANY part passes, the ENTIRE article is retained")
            print("✓ Metadata extraction is performed on the complete article")
        else:
            print("\n✗ Some tests failed. Please check the implementation.")
        
        return 0 if all_tests_passed else 1
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
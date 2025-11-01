import sys
import re
from typing import List, Dict, Any

# Multilingual/contextual keyword zones as per specification

# Patterns for structured pricing data (tables, lists, bullet points) - used only for metadata extraction
STRUCTURED_PATTERNS = [
    re.compile(r"(?:^|\n)[\*\-\u2022]\s*.+", re.MULTILINE),  # bullet points
    re.compile(r"(?:^|\n)\d+\.\s*.+", re.MULTILINE),         # numbered lists
    re.compile(r"(?:^|\n)\|.*\|", re.MULTILINE),             # markdown tables
    re.compile(r"(?:^|\n)(?:Contract|Date|Price|Volume|Index)\s*[:\-]\s*.+", re.IGNORECASE),  # key-value lines
]

# Sugar-related keywords for filtering - only these are used for the filtering decision
SUGAR_KEYWORDS = [
    "sugar", "sugarcane", "sugar cane", "sugar beet", "molasses", "sweetener", "sucrose",
    "glucose", "fructose", "saccharose", "raffinose", "whites", "NY11", "LSU", "LON No. 5",
    "raw sugar", "refined sugar", "brown sugar", "table sugar",
    # Multilingual - European languages
    "sucre", "azúcar", "zucchero", "açúcar", "Zucker", "sukker", "soker", "cukor",
    "cukier", "cukr", "sahara", "ζάχαρη", "cukor", "soker", "sugar", "sukker",
    # Multilingual - Asian languages
    "शक्कर", "चीनी", "চিনি", "சர்க்கரை", "చక్కరో", "ಸಕ್ಕರೆ", "പഞ്ചശര", "සීනි",
    "شکر", "سكر", "शक्कर", "चीनी", "gula", "gularen", "gula aren", "gula merah",
    "น้ำตาล", "น้ำตาลทราย", "อ้อย", "ตะกั่ว", "茶糖", "砂糖", "糖", "설탕", "설탕물",
    # Multilingual - Other major languages
    "şeker", "şekerli", "cukier", "cukrowy", "сахар", "сахарный", "цукор", "цукровий",
    "mishukozi", "asali", "sukari", "chini", "tumbura", "sukali", "sukari", "shakar",
    "shakkar", "misri", "khanda", "gud", "jaggery", "panela", "piloncillo", "rapadura"
]

# Context zone keywords - used only for metadata extraction, not for filtering
KEYWORDS = {
    "market": [
        "futures", "contract", "price", "market", "export", "exports", "exporter",
        "import", "imports", "importer", "shipment", "port", "tariff", "subsidy",
        "funds", "speculators", "commodity", "agriculture", "food", "crop", "yield", "farm", "plantation", "field", "season", "production", "output", "mill", "refinery", "processing", "supply", "demand"
    ],
    "supply_chain": [
        "harvest", "crushing", "yield", "production", "output", "mill", "plantation", "field", "farmer", "agricultural", "transport", "logistics", "storage", "inventory", "shipment", "supply", "demand"
    ],
    "event": [
        "ethanol", "mix", "weather", "drought", "frost", "rain", "monsoon",
        "climate", "El Niño", "La Niña", "storm", "flood", "heatwave", "hail", "cyclone", "typhoon", "disaster", "fire", "earthquake", "tornado", "crop loss", "damage", "alert", "warning"
    ],
    "region": [
        "Brazil", "Brasil", "Brazilian", "Center-South", "Centro-Sul", "India",
        "Indian", "Thailand", "Thai", "EU", "European Union", "UNICA",
        "International Sugar Organization", "ISO", "USDA", "Africa", "Asia", "Australia", "China", "Indonesia", "Pakistan", "Mexico", "Philippines", "Vietnam", "Russia", "Ukraine", "USA", "United States", "America"
    ]
}

# Compile regex for all keywords (case-insensitive, word boundaries)
def compile_keyword_patterns(keywords: List[str]) -> List[re.Pattern]:
    patterns = []
    for kw in keywords:
        # Handle keywords with spaces or special chars
        kw_escaped = re.escape(kw)
        # For multi-word keywords, allow any whitespace between words
        if " " in kw:
            kw_pattern = r"\b" + r"\s+".join(map(re.escape, kw.split())) + r"\b"
        else:
            kw_pattern = r"\b" + kw_escaped + r"\b"
        patterns.append(re.compile(kw_pattern, re.IGNORECASE))
    return patterns

# Compile patterns for sugar keywords (used for filtering)
SUGAR_KEYWORD_PATTERNS = compile_keyword_patterns(SUGAR_KEYWORDS)

# Compile patterns for context zones (used only for metadata extraction)
KEYWORD_PATTERNS = {zone: compile_keyword_patterns(words) for zone, words in KEYWORDS.items()}

def text_matches_keywords(text: str, patterns: List[re.Pattern]) -> bool:
    for pat in patterns:
        if pat.search(text):
            return True
    return False

# Monthly stats logging is preserved
import logging

def triage_filter(
    text: str,
    title: str = None,
    media_topic_passed: bool = True,
    min_length: int = 20,
    max_length: int = None,
    is_part: bool = False,
    part_number: int = None
) -> Dict[str, Any]:
    """
    Applies simplified Sugar Sentiment triage filtering logic.
    
    The filter now works as follows:
    1. Only checks for sugar-related keywords in title or text for filtering decision
    2. If no sugar-related keywords are found, the article is excluded
    3. Context zones, structured pricing, and name-entity recognition are used only for metadata extraction
    4. These features do not influence the filtering decision
    5. Enhanced to handle article parts with appropriate logging
    
    Args:
        text: Input text (str).
        title: Input title (str, optional).
        media_topic_passed: Whether IPTC MediaTopic pre-filtering passed (bool).
        min_length: Minimum text length for quality control.
        max_length: Maximum text length for quality control.
        is_part: Whether this text is a part of a larger article (bool).
        part_number: Which part this is (int, optional).
    Returns:
        Dict with filter result and metadata for matched zones.
    """
    # Part information for monthly stats
    import os
    part_info = f" (Part {part_number})" if is_part and part_number else " (Part)" if is_part else ""
    normalized_text = text
    normalized_title = title if title else ""
    # Combine title and text for keyword matching
    combined_content = f"{title} {text}" if title else text
    # Log part processing information for monthly stats
    if is_part:
        logger.info(f"Processing article part{part_info} with {len(text)} characters")
    
    result = {
        "passed": False,
        "reason": "",
        "matched_zones": [],
        "matched_keywords": [],
        "extracted_sugar_pricing": [],
        "is_part": is_part,
        "part_number": part_number
    }

    # Quality controls
    if not media_topic_passed:
        result["reason"] = "IPTC MediaTopic pre-filtering failed"
        return result
    if not isinstance(text, str) or not text.strip():
        result["reason"] = "Text is empty or not a string"
        return result
    if len(text) < min_length:
        result["reason"] = f"Text too short (<{min_length} chars)"
        return result
    if max_length is not None and len(text) > max_length:
        result["reason"] = f"Text too long (>{max_length} chars)"
        return result

    # SIMPLIFIED FILTERING LOGIC:
    # Only check for sugar-related keywords in title or text for filtering decision
    sugar_match = text_matches_keywords(combined_content, SUGAR_KEYWORD_PATTERNS)
    
    if not sugar_match:
        result["reason"] = "No sugar-related keywords found"
        return result
    
    # If sugar keywords are found, accept the article

    # EXTRACT METADATA (only for enrichment, not for filtering):
    
    # 1. Extract context zones metadata
    matched_zones = []
    matched_keywords = []
    for zone in ["market", "supply_chain", "event", "region"]:
        zone_patterns = KEYWORD_PATTERNS[zone]
        zone_matched = False
        for pat, kw in zip(zone_patterns, KEYWORDS[zone]):
            if pat.search(combined_content):
                matched_zones.append(zone)
                matched_keywords.append(kw)
                zone_matched = True
                break  # Only need one match per zone
    
    # 2. Extract structured pricing metadata
    extracted_sugar_pricing = []
    for struct_pat in STRUCTURED_PATTERNS:
        for match in struct_pat.finditer(text):
            line = match.group(0)
            # Only keep lines with sugar-related keywords
            if text_matches_keywords(line, SUGAR_KEYWORD_PATTERNS):
                extracted_sugar_pricing.append(line.strip())
    
    # If structured sugar pricing data found, add to result
    if extracted_sugar_pricing:
        result["extracted_sugar_pricing"] = extracted_sugar_pricing

    # Article passed the sugar keyword filter - set result and add metadata
    result["passed"] = True
    result["matched_zones"] = matched_zones  # Context zones metadata
    result["matched_keywords"] = matched_keywords  # Matched keywords metadata
    result["extracted_sugar_pricing"] = extracted_sugar_pricing  # Structured pricing metadata
    result["reason"] = "Passed sugar keyword filter"
    return result

# Example usage:
if __name__ == "__main__":
    sample_text = "Brazilian sugar exports are rising due to market price changes."
    print(triage_filter(sample_text))
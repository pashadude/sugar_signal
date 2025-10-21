import sys
import re
from typing import List, Dict, Any

# Multilingual/contextual keyword zones as per specification

# Exclusion keywords for non-sugar commodities and generic market news
EXCLUSION_KEYWORDS = [
    "copper", "cocoa", "cotton", "oil", "gas", "crude", "energy", "aluminum", "nickel",
    "zinc", "lead", "tin", "wheat", "corn", "soy", "soybean", "coffee", "tea", "rubber",
    "palm", "gold", "silver", "platinum", "palladium", "iron", "steel", "coal", "uranium",
    "natural gas", "petroleum", "oat", "barley", "livestock", "dairy", "meat", "poultry",
    "generic market news", "macro", "macro-economic", "inflation", "interest rate", "currency"
]

EXCLUSION_PATTERNS = [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in EXCLUSION_KEYWORDS]

# Patterns for structured pricing data (tables, lists, bullet points)
STRUCTURED_PATTERNS = [
    re.compile(r"(?:^|\n)[\*\-\u2022]\s*.+", re.MULTILINE),  # bullet points
    re.compile(r"(?:^|\n)\d+\.\s*.+", re.MULTILINE),         # numbered lists
    re.compile(r"(?:^|\n)\|.*\|", re.MULTILINE),             # markdown tables
    re.compile(r"(?:^|\n)(?:Contract|Date|Price|Volume|Index)\s*[:\-]\s*.+", re.IGNORECASE),  # key-value lines
]

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
    ],
    "main": [
        "sugar", "sugarcane", "sugar cane", "sugar beet", "molasses", "sweetener", "sucrose", "glucose", "fructose", "saccharose", "raffinose", "whites", "NY11", "LSU", "LON No. 5", "raw sugar", "refined sugar", "brown sugar", "table sugar"
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

KEYWORD_PATTERNS = {zone: compile_keyword_patterns(words) for zone, words in KEYWORDS.items()}

def text_matches_keywords(text: str, patterns: List[re.Pattern]) -> bool:
    for pat in patterns:
        if pat.search(text):
            return True
    return False

# DEBUG LOGGING: Print detailed triage info for each article
import logging
logger = logging.getLogger("sugar_triage_debug")
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def triage_filter(
    text: str,
    media_topic_passed: bool = True,
    min_length: int = 20,
    max_length: int = None
) -> Dict[str, Any]:
    """
    Applies Sugar Sentiment triage filtering logic.
    Args:
        text: Input text (str).
        media_topic_passed: Whether IPTC MediaTopic pre-filtering passed (bool).
        min_length: Minimum text length for quality control.
        max_length: Maximum text length for quality control.
    Returns:
        Dict with filter result and matched zones.
    """
    # Only log full text if not running as part of sugar_news_fetcher CLI
    import os
    if not any("sugar_news_fetcher" in arg for arg in sys.argv):
        logger.debug("TRIAGE INPUT: %r", text)
        logger.debug("STAGE: INPUT | TEXT: %r", text)
    # --- Begin detailed per-stage logging ---
    normalized_text = text
    if not any("sugar_news_fetcher" in arg for arg in sys.argv):
        logger.debug("STAGE: INPUT | TEXT: %r", normalized_text)
    result = {
        "passed": False,
        "reason": "",
        "matched_zones": [],
        "matched_keywords": [],
        "extracted_sugar_pricing": []
    }

    # Quality controls
    if not media_topic_passed:
        result["reason"] = "IPTC MediaTopic pre-filtering failed"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("REJECT: %s", result["reason"])
        return result
    if not isinstance(text, str) or not text.strip():
        result["reason"] = "Text is empty or not a string"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("REJECT: %s", result["reason"])
        return result
    if len(text) < min_length:
        result["reason"] = f"Text too short (<{min_length} chars)"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("REJECT: %s", result["reason"])
        return result
    if max_length is not None and len(text) > max_length:
        result["reason"] = f"Text too long (>{max_length} chars)"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("REJECT: %s", result["reason"])
        return result

    # Check for main keywords (must match at least one)
    main_match = text_matches_keywords(text, KEYWORD_PATTERNS["main"])
    
    # If no main keywords, check for exclusion keywords
    if not main_match:
        for pat in EXCLUSION_PATTERNS:
            if pat.search(text):
                result["reason"] = f"Excluded by exclusion keyword: '{pat.pattern}'"
                if not any("sugar_news_fetcher" in arg for arg in sys.argv):
                    logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
                else:
                    logger.debug("REJECT: %s", result["reason"])
                return result
        
        # If no main keywords and no exclusion keywords, reject
        result["reason"] = "No main sugar-related keywords found"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("REJECT: %s", result["reason"])
        return result
    
    # If main keywords found, check for secondary filter (event+agriculture)
    event_match = text_matches_keywords(text, KEYWORD_PATTERNS["event"])
    agri_match = (
        text_matches_keywords(text, KEYWORD_PATTERNS["market"]) or
        text_matches_keywords(text, KEYWORD_PATTERNS["supply_chain"])
    )
    if event_match and agri_match:
        result["reason"] = "Passed secondary filter: event+agriculture context"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("PASS: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("PASS: %s", result["reason"])
        result["passed"] = True
        result["matched_zones"] = []
        result["matched_keywords"] = []
        result["extracted_sugar_pricing"] = []
        return result

    # Check context zones
    matched_zones = []
    matched_keywords = []
    for zone in ["market", "supply_chain", "event", "region"]:
        zone_patterns = KEYWORD_PATTERNS[zone]
        zone_matched = False
        for pat, kw in zip(zone_patterns, KEYWORDS[zone]):
            if pat.search(text):
                matched_zones.append(zone)
                matched_keywords.append(kw)
                logger.debug("STAGE: CONTEXT_ZONE | ZONE: %s | MATCHED: %s", zone, kw)
                zone_matched = True
                break  # Only need one match per zone
        if not zone_matched:
            logger.debug("STAGE: CONTEXT_ZONE | ZONE: %s | MATCHED: None", zone)

    if not matched_zones:
        result["reason"] = "No context zone keywords found"
        if not any("sugar_news_fetcher" in arg for arg in sys.argv):
            logger.debug("REJECT: %s | TEXT: %r", result["reason"], normalized_text)
        else:
            logger.debug("REJECT: %s", result["reason"])
        return result

    # Detect and extract structured sugar pricing data
    extracted_sugar_pricing = []
    for struct_pat in STRUCTURED_PATTERNS:
        for match in struct_pat.finditer(text):
            line = match.group(0)
            # Only keep lines with sugar-related main keywords
            if text_matches_keywords(line, KEYWORD_PATTERNS["main"]):
                # Exclude if line contains non-sugar commodity
                if not any(pat.search(line) for pat in EXCLUSION_PATTERNS):
                    extracted_sugar_pricing.append(line.strip())
                    logger.debug("STAGE: STRUCTURED_PRICING | MATCHED: %r", line.strip())
    # If structured sugar pricing data found, add to result
    if extracted_sugar_pricing:
        result["extracted_sugar_pricing"] = extracted_sugar_pricing
    else:
        logger.debug("STAGE: STRUCTURED_PRICING | MATCHED: None")

    # Passed all filters
    result["passed"] = True
    result["matched_zones"] = matched_zones
    result["matched_keywords"] = matched_keywords
    result["reason"] = "Passed all triage filters"
    logger.debug("PASS: matched_zones=%r matched_keywords=%r extracted_sugar_pricing=%r", matched_zones, matched_keywords, extracted_sugar_pricing)
    return result

# Example usage:
if __name__ == "__main__":
    sample_text = "Brazilian sugar exports are rising due to market price changes."
    print(triage_filter(sample_text))
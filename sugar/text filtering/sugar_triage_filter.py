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
        "funds", "speculators"
    ],
    "supply_chain": [
        "harvest", "crushing", "yield", "production", "output", "mill"
    ],
    "event": [
        "ethanol", "mix", "weather", "drought", "frost", "rain", "monsoon",
        "climate", "El Niño", "La Niña"
    ],
    "region": [
        "Brazil", "Brasil", "Brazilian", "Center-South", "Centro-Sul", "India",
        "Indian", "Thailand", "Thai", "EU", "European Union", "UNICA",
        "International Sugar Organization", "ISO", "USDA"
    ],
    "main": [
        "sugar", "sugarcane", "sugar beet", "whites", "NY11", "LSU", "LON No. 5"
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

def triage_filter(
    text: str,
    media_topic_passed: bool = True,
    min_length: int = 20,
    max_length: int = 10000
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
        return result
    if not isinstance(text, str) or not text.strip():
        result["reason"] = "Text is empty or not a string"
        return result
    if len(text) < min_length:
        result["reason"] = f"Text too short (<{min_length} chars)"
        return result
    if len(text) > max_length:
        result["reason"] = f"Text too long (>{max_length} chars)"
        return result

    # Exclude non-sugar commodities and generic market news
    for pat in EXCLUSION_PATTERNS:
        if pat.search(text):
            result["reason"] = "Excluded non-sugar commodity or generic market news"
            return result

    # Check for main keywords (must match at least one)
    if not text_matches_keywords(text, KEYWORD_PATTERNS["main"]):
        result["reason"] = "No main sugar-related keywords found"
        return result

    # Check context zones
    matched_zones = []
    matched_keywords = []
    for zone in ["market", "supply_chain", "event", "region"]:
        zone_patterns = KEYWORD_PATTERNS[zone]
        for pat, kw in zip(zone_patterns, KEYWORDS[zone]):
            if pat.search(text):
                matched_zones.append(zone)
                matched_keywords.append(kw)
                break  # Only need one match per zone

    if not matched_zones:
        result["reason"] = "No context zone keywords found"
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
    # If structured sugar pricing data found, add to result
    if extracted_sugar_pricing:
        result["extracted_sugar_pricing"] = extracted_sugar_pricing

    # Passed all filters
    result["passed"] = True
    result["matched_zones"] = matched_zones
    result["matched_keywords"] = matched_keywords
    result["reason"] = "Passed all triage filters"
    return result

# Example usage:
if __name__ == "__main__":
    sample_text = "Brazilian sugar exports are rising due to market price changes."
    print(triage_filter(sample_text))
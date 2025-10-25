# Sugar News Pipeline Triage Filters Analysis

## Overview

This document provides a comprehensive analysis of the triage filters used in the sugar news pipeline, as implemented in [`sugar_triage_filter.py`](ShinkaEvolve/shinka/examples/sugar/backend/text_filtering/sugar_triage_filter.py). The triage filter is a critical component that determines whether an article is relevant to sugar by applying multiple layers of filtering criteria.

## Filter Architecture

The triage filter operates in a sequential manner, applying different types of filters in a specific order:

1. **Quality Control Filters** - Basic validation checks
2. **Main Keyword Filter** - Primary sugar-related terms
3. **Exclusion Filter** - Non-sugar commodity terms
4. **Secondary Filter** - Event + Agriculture context combination
5. **Context Zone Filters** - Thematic keyword categories
6. **Structured Data Filter** - Pricing and market data extraction

## 1. Quality Control Filters

### Purpose
These filters perform basic validation to ensure the input text meets minimum quality standards before processing.

### Filter Criteria
- **Media Topic Check**: Verifies if IPTC MediaTopic pre-filtering passed
- **Text Validation**: Ensures input is a non-empty string
- **Minimum Length**: Requires at least 20 characters (configurable)
- **Maximum Length**: Optional upper limit on text length (configurable)

### Implementation
```python
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
```

## 2. Main Keyword Filter

### Purpose
Identifies articles that contain primary sugar-related terms. This is the first and most important filter that determines if an article could be about sugar.

### Keywords
The main keywords include:
- **Core Terms**: "sugar", "sugarcane", "sugar cane", "sugar beet"
- **Byproducts**: "molasses", "sweetener", "sucrose", "glucose", "fructose"
- **Chemical Compounds**: "saccharose", "raffinose"
- **Market Terms**: "whites", "NY11", "LSU", "LON No. 5"
- **Product Types**: "raw sugar", "refined sugar", "brown sugar", "table sugar"

### Implementation
The filter uses regex patterns with word boundaries to ensure precise matching:
```python
main_match = text_matches_keywords(text, KEYWORD_PATTERNS["main"])
```

### How It Works
- Each keyword is compiled into a regex pattern with word boundaries
- Multi-word keywords (like "sugar cane") are handled with flexible whitespace matching
- Search is case-insensitive
- At least one main keyword must be present for an article to pass this filter

## 3. Exclusion Filter

### Purpose
Filters out articles that mention non-sugar commodities or generic market news, even if they contain sugar-related terms.

### Exclusion Keywords
The exclusion list includes:
- **Other Commodities**: "copper", "cocoa", "cotton", "oil", "gas", "crude", "energy", "aluminum", "nickel", "zinc", "lead", "tin", "wheat", "corn", "soy", "soybean", "coffee", "tea", "rubber", "palm"
- **Precious Metals**: "gold", "silver", "platinum", "palladium"
- **Industrial Metals**: "iron", "steel", "coal", "uranium"
- **Energy**: "natural gas", "petroleum"
- **Grains**: "oat", "barley"
- **Livestock**: "livestock", "dairy", "meat", "poultry"
- **Generic Terms**: "generic market news", "macro", "macro-economic", "inflation", "interest rate", "currency"

### Implementation
```python
if not main_match:
    for pat in EXCLUSION_PATTERNS:
        if pat.search(text):
            result["reason"] = f"Excluded by exclusion keyword: '{pat.pattern}'"
            return result
```

### How It Works
- Only applied if no main sugar keywords are found
- If any exclusion keyword is present, the article is immediately rejected
- Uses compiled regex patterns for efficient searching
- Case-insensitive matching with word boundaries

## 4. Secondary Filter (Event + Agriculture)

### Purpose
Provides a fast-pass mechanism for articles that contain both event-related and agriculture-related keywords, indicating strong contextual relevance to sugar.

### Filter Logic
An article passes this filter if it contains:
- At least one keyword from the "event" category AND
- At least one keyword from either "market" or "supply_chain" categories

### Implementation
```python
event_match = text_matches_keywords(text, KEYWORD_PATTERNS["event"])
agri_match = (
    text_matches_keywords(text, KEYWORD_PATTERNS["market"]) or
    text_matches_keywords(text, KEYWORD_PATTERNS["supply_chain"])
)
if event_match and agri_match:
    result["reason"] = "Passed secondary filter: event+agriculture context"
    result["passed"] = True
    return result
```

### How It Works
- This is an optimization to quickly identify highly relevant articles
- Bypasses the need for detailed context zone analysis
- Focuses on articles that discuss both events (like weather) and agricultural/market aspects

## 5. Context Zone Filters

### Purpose
Evaluates the thematic context of articles by checking for keywords in specific categories. Articles must match at least one context zone to pass.

### Context Zones and Keywords

#### A. Market Zone
**Purpose**: Identifies articles discussing market dynamics, trade, and economic aspects of sugar.

**Keywords**:
- **Trading**: "futures", "contract", "price", "market"
- **Trade**: "export", "exports", "exporter", "import", "imports", "importer"
- **Logistics**: "shipment", "port", "tariff", "subsidy"
- **Finance**: "funds", "speculators"
- **General**: "commodity", "agriculture", "food", "crop", "yield", "farm", "plantation", "field", "season", "production", "output", "mill", "refinery", "processing", "supply", "demand"

#### B. Supply Chain Zone
**Purpose**: Focuses on production, processing, and logistics aspects of the sugar industry.

**Keywords**:
- **Production**: "harvest", "crushing", "yield", "production", "output"
- **Facilities**: "mill", "plantation", "field"
- **People**: "farmer", "agricultural"
- **Logistics**: "transport", "logistics", "storage", "inventory", "shipment"
- **Economics**: "supply", "demand"

#### C. Event Zone
**Purpose**: Captures articles about events that impact sugar production or markets.

**Keywords**:
- **Energy**: "ethanol", "mix"
- **Weather**: "weather", "drought", "frost", "rain", "monsoon", "climate"
- **Climate Patterns**: "El Niño", "La Niña"
- **Extreme Weather**: "storm", "flood", "heatwave", "hail", "cyclone", "typhoon"
- **Disasters**: "disaster", "fire", "earthquake", "tornado"
- **Impact**: "crop loss", "damage", "alert", "warning"

#### D. Region Zone
**Purpose**: Identifies articles mentioning key sugar-producing regions and organizations.

**Keywords**:
- **Countries**: "Brazil", "Brasil", "Brazilian", "India", "Indian", "Thailand", "Thai"
- **Regions**: "Center-South", "Centro-Sul", "Africa", "Asia", "Australia", "China", "Indonesia", "Pakistan", "Mexico", "Philippines", "Vietnam", "Russia", "Ukraine", "USA", "United States", "America"
- **Organizations**: "EU", "European Union", "UNICA", "International Sugar Organization", "ISO", "USDA"

### Implementation
```python
matched_zones = []
matched_keywords = []
for zone in ["market", "supply_chain", "event", "region"]:
    zone_patterns = KEYWORD_PATTERNS[zone]
    zone_matched = False
    for pat, kw in zip(zone_patterns, KEYWORDS[zone]):
        if pat.search(text):
            matched_zones.append(zone)
            matched_keywords.append(kw)
            zone_matched = True
            break  # Only need one match per zone
```

### How It Works
- Each zone is checked independently
- Only one keyword match per zone is needed to count that zone as matched
- Articles must match at least one zone to pass the filter
- All matched zones and keywords are recorded for analysis

## 6. Structured Data Filter

### Purpose
Extracts structured pricing and market data from articles, focusing on tables, lists, and key-value formats that contain sugar-related information.

### Structured Patterns
The filter recognizes several types of structured data:
- **Bullet Points**: Lines starting with *, -, or •
- **Numbered Lists**: Lines starting with numbers followed by periods
- **Markdown Tables**: Lines containing pipe characters (|)
- **Key-Value Lines**: Lines with keys like "Contract", "Date", "Price", "Volume", "Index"

### Implementation
```python
STRUCTURED_PATTERNS = [
    re.compile(r"(?:^|\n)[\*\-\u2022]\s*.+", re.MULTILINE),  # bullet points
    re.compile(r"(?:^|\n)\d+\.\s*.+", re.MULTILINE),         # numbered lists
    re.compile(r"(?:^|\n)\|.*\|", re.MULTILINE),             # markdown tables
    re.compile(r"(?:^|\n)(?:Contract|Date|Price|Volume|Index)\s*[:\-]\s*.+", re.IGNORECASE),  # key-value lines
]

extracted_sugar_pricing = []
for struct_pat in STRUCTURED_PATTERNS:
    for match in struct_pat.finditer(text):
        line = match.group(0)
        # Only keep lines with sugar-related main keywords
        if text_matches_keywords(line, KEYWORD_PATTERNS["main"]):
            # Exclude if line contains non-sugar commodity
            if not any(pat.search(line) for pat in EXCLUSION_PATTERNS):
                extracted_sugar_pricing.append(line.strip())
```

### How It Works
- Scans text for structured data patterns
- For each matched structure, checks if it contains sugar-related keywords
- Excludes structures that mention non-sugar commodities
- Extracts and stores relevant structured data for further analysis

## Filter Workflow Summary

The complete filtering process follows this decision tree:

1. **Quality Control**
   - Fail if: MediaTopic failed, text empty/invalid, too short, or too long
   - Continue if: All quality checks pass

2. **Main Keyword Check**
   - Fail if: No main sugar keywords found AND exclusion keywords present
   - Continue if: Main sugar keywords found

3. **Secondary Filter (Event + Agriculture)**
   - Pass immediately if: Both event and agriculture keywords found
   - Continue if: Secondary filter not triggered

4. **Context Zone Check**
   - Fail if: No context zones matched
   - Pass if: At least one context zone matched

5. **Structured Data Extraction**
   - Extract any structured pricing data present
   - Pass regardless of structured data findings

## Example Filter Applications

### Example 1: Clear Sugar News
**Text**: "Brazilian sugar exports are rising due to market price changes."
- **Quality Control**: Pass
- **Main Keywords**: "sugar" ✓
- **Exclusion Filter**: Not triggered (has main keywords)
- **Secondary Filter**: Not triggered
- **Context Zones**: "market", "region" ✓
- **Result**: PASS

### Example 2: Non-Sugar Commodity
**Text**: "Copper prices are rising in the commodity market."
- **Quality Control**: Pass
- **Main Keywords**: None ✗
- **Exclusion Filter**: "copper" found → REJECT
- **Result**: FAIL

### Example 3: Weather Impact on Sugar
**Text**: "Sugar production in Brazil affected by drought conditions."
- **Quality Control**: Pass
- **Main Keywords**: "sugar" ✓
- **Exclusion Filter**: Not triggered
- **Secondary Filter**: "drought" (event) + "production" (agriculture) ✓
- **Result**: PASS (fast-track)

### Example 4: Generic Market News
**Text**: "Generic market news about inflation and interest rates."
- **Quality Control**: Pass
- **Main Keywords**: None ✗
- **Exclusion Filter**: "generic market news" found → REJECT
- **Result**: FAIL

## Key Features and Optimizations

### 1. Regex Pattern Compilation
All keyword patterns are pre-compiled into regex objects for efficient matching:
```python
KEYWORD_PATTERNS = {zone: compile_keyword_patterns(words) for zone, words in KEYWORDS.items()}
```

### 2. Multi-word Keyword Handling
Special handling for keywords with spaces:
```python
if " " in kw:
    kw_pattern = r"\b" + r"\s+".join(map(re.escape, kw.split())) + r"\b"
else:
    kw_pattern = r"\b" + kw_escaped + r"\b"
```

### 3. Debug Logging
Comprehensive logging for troubleshooting:
```python
logger.debug("STAGE: CONTEXT_ZONE | ZONE: %s | MATCHED: %s", zone, kw)
```

### 4. Flexible Configuration
Key parameters are configurable:
- `min_length`: Minimum text length
- `max_length`: Maximum text length
- `media_topic_passed`: External pre-filter status

## Testing and Validation

The filter includes comprehensive test cases covering:
- Valid sugar news with various contexts
- Non-sugar commodity news
- Edge cases (short text, empty text)
- Structured data extraction
- Multi-language support considerations

Test results are saved to JSON files for detailed analysis and regression testing.

## Conclusion

The sugar news pipeline triage filter implements a multi-layered approach to identify relevant articles with high precision. By combining quality controls, keyword matching, exclusion rules, and context analysis, it effectively filters out noise while capturing diverse sugar-related content. The structured data extraction capability adds value by identifying pricing and market information within articles.

The filter's design allows for easy maintenance and expansion, with keywords and rules organized in clear categories. This comprehensive approach ensures that the pipeline captures sugar news from various angles - from market dynamics and production issues to weather impacts and regional developments.
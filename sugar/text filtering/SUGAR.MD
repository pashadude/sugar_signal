# Sugar Sentiment Classification Workflow

## Overview

The Sugar Sentiment Classification system is a modular, extensible pipeline designed to robustly analyze and classify sentiment in user-generated text and to extract, normalize, and validate sugar-related pricing data. The workflow is structured to maximize accuracy, maintainability, and adaptability to evolving language and market data trends. It consists of the following primary stages:

1. **Sugar Pricing Data Extraction & Normalization Pipeline**: Identifies, extracts, and standardizes sugar pricing data, index summaries, and volume reports, even when embedded among other commodities.
2. **Triage/Filtering**: Screens and routes input for further processing or exclusion.
3. **Language Normalization**: Standardizes text, corrects errors, and prepares data for analysis.
4. **Specialist Model Selection**: Dynamically chooses the most appropriate sentiment model based on content and context.
5. **Training Data Generation**: Curates and augments labeled data for continuous model improvement.

Each stage is implemented as a distinct, testable module, supporting iterative development and targeted enhancements.

---

## 1. Sugar Pricing Data Extraction & Normalization Pipeline

### Overview

The enhanced pipeline robustly identifies, extracts, and routes sugar-related pricing tables, index summaries, and volume reports—even when these are embedded among other commodities or within generic market news. This enables precise downstream normalization and analysis, supporting both operational and stakeholder needs.

### Identification & Extraction Logic

- **Commodity-Specific Filtering:**  
  Uses comprehensive keyword and regex patterns to detect sugar-related content, including contracts (NY11, LSU, LON No. 5), regions (Brazil, India, Thailand), and market events (harvest, drought, export/import).
- **Structured Format Recognition:**  
  Recognizes and extracts pricing data from:
  - Markdown tables (e.g., `| Contract | Date | Price | Volume |`)
  - Numbered and bulleted lists
  - Key-value lines (e.g., `Contract: NY11`, `Price: 27.50`)
- **Contextual Extraction:**  
  Only lines containing sugar-related main keywords are extracted, even if mixed with other commodities.

### Exclusion Logic

- **Non-Sugar Commodity Filtering:**  
  Lines or sections mentioning non-sugar commodities (e.g., copper, cocoa, oil, wheat) or generic market news are excluded using a maintained exclusion keyword list and regex patterns.
- **Quality Controls:**  
  Filters out empty, malformed, or excessively short/long input, and ensures only actionable data proceeds.

### Example

Extracted from a mixed table:
```
| Contract | Date       | Price  | Volume |
|----------|------------|--------|--------|
| NY11     | 2025-10-19 | 27.50  | 12000  |   <-- Extracted
| Copper   | 2025-10-19 | 8.50   | 5000   |   <-- Excluded
```

**References:**  
- [`sugar_triage_filter.py`](sugar_triage_filter.py:1) — triage logic and exclusion rules  
- [`triage_filter_validation_test.py`](triage_filter_validation_test.py:1) — validation cases for extraction and exclusion

---

## 2. Sugar Pricing Data Normalization Pipeline

### Overview

The normalization pipeline standardizes extracted sugar pricing data, ensuring consistency, accuracy, and preservation of essential context for downstream analysis and reporting.

### Standardization & Context Preservation

- **Structured Data Extraction:**  
  Extracted lines are parsed to identify and standardize key fields:
  - **Contract** (e.g., NY11, LSU, LON No. 5)
  - **Date** (multiple formats supported)
  - **Price** (numeric, currency-agnostic)
  - **Volume** (numeric)
  - **Index** (numeric, if present)
  - **Raw Line** (original text for traceability)
- **Multilingual & Noisy Input Handling:**  
  - Auto-detects and translates non-English text to English.
  - Corrects typos, normalizes slang, and standardizes punctuation.
  - Handles transliterations, mixed-language, and ambiguous terms.
- **Edge Case Management:**  
  - Robust to template overlap, abbreviation ambiguity, and formatting noise.
  - Preserves original context for audit and error recovery.

### Example Output

A normalized sugar pricing entry:
```json
{
  "contract": "NY11",
  "date": "2025-10-19",
  "price": "27.50",
  "volume": "12000",
  "index": null,
  "raw_line": "| NY11     | 2025-10-19 | 27.50  | 12000  |"
}
```

**References:**  
- [`language_normalization.py`](language_normalization.py:1) — normalization logic and context preservation  
- [`language_normalization_validation_test.py`](language_normalization_validation_test.py:1) — validation cases for normalization and edge case handling

---

## 3. Triage/Filtering

### Purpose & Rationale

- **Efficiency**: Early exclusion of irrelevant, malformed, or non-actionable input reduces computational load.
- **Quality Control**: Ensures only suitable data proceeds to downstream stages, improving overall system reliability.

### Design & Implementation

- **Keyword Pattern Compilation**: Uses [`compile_keyword_patterns()`](sugar_triage_filter.py:29) to build efficient regex patterns from domain-specific keywords.
- **Text Matching**: [`text_matches_keywords()`](sugar_triage_filter.py:44) checks if input text matches any compiled patterns.
- **Main Filter Logic**: [`triage_filter()`](sugar_triage_filter.py:50) orchestrates the filtering process, applying exclusion/inclusion rules and logging decisions.

### Error Handling & Edge Cases

- Handles malformed input gracefully, logging and skipping problematic entries.
- Configurable keyword lists allow rapid adaptation to new spam or irrelevant content patterns.
- Edge cases (e.g., empty strings, excessive length, non-textual input) are explicitly checked and filtered.

### Iterative Improvements

- Validation tests (see `triage_filter_validation_test.py`) are used to refine filter rules and catch new edge cases as they emerge.
- User and stakeholder feedback is incorporated to adjust filtering sensitivity and coverage.

---

## 4. Language Normalization

### Purpose & Rationale

- **Standardization**: Converts diverse, noisy user input into a consistent format for analysis.
- **Robustness**: Handles slang, typos, code-switching, and non-standard punctuation.

### Design & Implementation

Implemented as [`LanguageNormalizationPipeline`](language_normalization.py:44), with the following modular steps:

- **Translation**: `_translate_to_english()` auto-detects and translates non-English text.
- **Typo Correction**: `_correct_typos()` applies spelling correction algorithms.
- **Slang & Synonym Mapping**: `_map_slang_synonyms()` replaces informal or domain-specific terms with standardized equivalents.
- **Punctuation Normalization**: `_normalize_punctuation()` ensures consistent use of punctuation and spacing.
- **Edge Case Handling**: `_handle_edge_cases()` addresses rare or ambiguous input scenarios.

The main entry point is [`normalize(text)`](language_normalization.py:71), which sequentially applies all steps.

### Error Handling & Edge Cases

- Each step is wrapped in try/except blocks to prevent pipeline failure on unexpected input.
- Logs errors and returns best-effort normalized text, or flags input for manual review if normalization is not possible.
- Special handling for mixed-language, emoji, and non-standard Unicode input.

### Iterative Improvements

- Extensive validation via [`language_normalization_validation_test.py`](language_normalization_validation_test.py:3) ensures coverage of new slang, typos, and language trends.
- Feedback loops from model misclassifications and user reports drive updates to slang dictionaries and normalization rules.

---

## 5. Specialist Model Selection

### Purpose & Rationale

- **Accuracy**: Different sentiment models may excel on different domains, languages, or content types.
- **Adaptability**: Enables rapid integration of new or improved models for specific use cases.

### Design & Implementation

- After normalization, input is analyzed for domain, language, and content features.
- A routing mechanism selects the most appropriate specialist model (e.g., general sentiment, sarcasm detection, domain-specific sentiment).
- Models are versioned and can be A/B tested for continuous improvement.

### Error Handling & Edge Cases

- Fallback to a default model if specialist selection fails or confidence is low.
- Logs all routing decisions for audit and future tuning.

---

## 6. Training Data Generation

### Purpose & Rationale

- **Continuous Improvement**: High-quality, diverse training data is essential for model accuracy and robustness.
- **Automation**: Reduces manual labeling effort and accelerates iteration.

### Design & Implementation

- Samples are selected from filtered and normalized input, with priority given to edge cases and misclassified examples.
- Semi-automated labeling tools assist human annotators.
- Data augmentation techniques (e.g., paraphrasing, back-translation) increase dataset diversity.

### Error Handling & Edge Cases

- Automated checks for label consistency and data quality.
- Edge cases are flagged for expert review and, if necessary, used to update normalization or filtering logic.

---

## 7. Validation Improvements & Integration Readiness

### Validation Enhancements

- **Comprehensive Test Coverage:**  
  - Validation suites cover triage/filtering, exclusion logic, structured extraction, and normalization.
  - Test cases include multilingual input, mixed-commodity tables, noisy and edge-case scenarios.
  - Automated checks ensure only sugar-relevant data is extracted and normalized.
- **Continuous Feedback Loop:**  
  - Misclassifications and extraction errors are tracked and used to refine keyword lists, exclusion rules, and normalization logic.
  - Stakeholder and user feedback incorporated for ongoing improvement.

### Integration Readiness

- **Modular Design:**  
  - Each pipeline stage (triage/filtering, normalization) is independently testable and documented.
  - Ready for integration with downstream analytics, reporting, and model training workflows.
- **Extensibility:**  
  - Easily adaptable to new commodity-specific requirements or evolving market data formats.
  - Supports onboarding of new contributors via clear documentation and test-driven development.

**References:**  
- [`triage_filter_validation_test.py`](triage_filter_validation_test.py:1) — triage/filtering validation  
- [`language_normalization_validation_test.py`](language_normalization_validation_test.py:1) — normalization validation

---

## 8. Recommendations for Future Enhancements

- **Slang Dictionary Expansion**: Regularly update slang and synonym lists to keep pace with evolving language.
- **Mixed-Language Handling**: Enhance detection and normalization for code-switching and multilingual input.
- **Contextual Sentiment**: Integrate context-aware models for improved accuracy on ambiguous or sarcastic input.
- **Explainability**: Add model interpretability features for transparency and trust.
- **Automated Feedback Loops**: Streamline the process of incorporating user feedback into model and rule updates.

---

## 9. Onboarding & Contribution Guidelines

- Each module is independently testable and documented.
- New contributors should start by reviewing the validation test files and running the test suites.
- For enhancements, propose changes via pull request and include new tests for any added logic or edge cases.
- Stakeholders are encouraged to provide feedback on misclassifications and suggest new slang or domain-specific terms.

---

**For questions or to contribute, please refer to the module-specific documentation and test files.**
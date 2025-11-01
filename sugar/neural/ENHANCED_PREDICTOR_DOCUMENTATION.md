# Enhanced Commodity Sentiment Predictor Documentation

## Overview

The `predictor.py` file has been enhanced to include the following new features:

1. **Topics as an additional input parameter**: The predictor now accepts a list of topics to provide additional context for sentiment analysis.
2. **ClickHouse integration**: Prompts and analysis results can now be saved to the `news.prompts` table in ClickHouse.
3. **Enhanced testing**: New test scripts have been created to test the enhanced functionality with real Sugar news articles.

## Changes Made

### 1. Enhanced CommoditySentimentPredictor Class

#### New Constructor Parameters
- `save_prompts` (bool, optional): Whether to save prompts to ClickHouse news.prompts table. Default is False.

#### New Methods
- `_create_user_prompt()`: Now accepts an optional `topics` parameter to include topics in the user prompt.
- `analyze_sentiment()`: Now accepts optional `topics` and `article_id` parameters.
- `batch_analyze()`: Now accepts optional `topics_list` and `article_ids` parameters.
- `_save_prompts_to_clickhouse()`: Saves prompts and analysis results to ClickHouse.
- `_ensure_prompts_table_exists()`: Ensures the news.prompts table exists in ClickHouse.

#### Enhanced Properties
- `clickhouse_client`: Lazy initialization of the ClickHouse client when `save_prompts` is enabled.

### 2. Command-Line Interface Enhancements

The command-line interface now supports:
- `--topics`: Comma-separated list of topics
- `--save-prompts`: Flag to enable saving prompts to ClickHouse
- `--article-id`: Article ID for saving prompts

### 3. New Test Script

A new test script `test_sugar_news_with_topics.py` has been created that:
- Connects to ClickHouse database
- Retrieves Sugar news articles from the news.news table
- Extracts topics from the metadata field
- Uses the enhanced predictor to analyze sentiment with topics
- Saves results to the news.prompts table
- Provides a summary of the analysis

## Usage Examples

### Basic Usage with Topics

```python
from predictor import CommoditySentimentPredictor

# Initialize predictor
predictor = CommoditySentimentPredictor()

# Analyze sentiment with topics
text = "Sugar prices surged due to supply constraints from Brazil."
title = "Sugar Market Update"
commodity = "Sugar"
topics = ["agriculture", "weather", "supply"]

result = predictor.analyze_sentiment(
    text=text,
    title=title,
    commodity=commodity,
    topics=topics
)

print(f"Sentiment: {result['sentiment']}")
print(f"Confidence: {result['confidence']}")
print(f"Reasoning: {result['reasoning']}")
```

### Batch Analysis with Topics

```python
# Batch analysis with topics
texts = [
    "Sugar prices fell due to increased production.",
    "The sugar market remains stable.",
    "Positive outlook for sugar as demand increases."
]

titles = [
    "Sugar Prices Decline",
    "Sugar Market Stability",
    "Sugar Demand Increases"
]

commodities = ["Sugar", "Sugar", "Sugar"]
topics_list = [
    ["production", "supply"],
    ["market", "stability"],
    ["demand", "forecast"]
]

results = predictor.batch_analyze(
    texts=texts,
    titles=titles,
    commodities=commodities,
    topics_list=topics_list
)

for i, result in enumerate(results):
    print(f"Article {i+1}: {result['sentiment']} (confidence: {result['confidence']:.2f})")
```

### Saving Prompts to ClickHouse

```python
# Initialize predictor with ClickHouse saving enabled
predictor = CommoditySentimentPredictor(save_prompts=True)

# Analyze sentiment with article ID for saving
result = predictor.analyze_sentiment(
    text="Sugar prices surged due to supply constraints.",
    title="Sugar Market Update",
    commodity="Sugar",
    topics=["agriculture", "supply"],
    article_id="unique-article-id-123"
)

# The prompts and results will be automatically saved to news.prompts table
```

### Command-Line Usage

```bash
# Basic usage with topics
python predictor.py --text "Sugar prices are rising" --title "Market Update" --commodity "Sugar" --topics "agriculture,weather"

# Save prompts to ClickHouse
python predictor.py --text "Sugar prices are rising" --title "Market Update" --commodity "Sugar" --topics "agriculture,weather" --save-prompts --article-id "article-123"

# Using input file
python predictor.py --file article.txt --title "Market Analysis" --commodity "Sugar" --topics "market,forecast" --save-prompts --article-id "article-456"
```

## Testing the Enhanced Functionality

### Running the Basic Tests

```bash
# Test basic functionality (no API calls)
python test_predictor.py
```

### Running Integration Tests

```bash
# Test with real API calls (requires NEBIUS_API_KEY)
python test_integration.py
```

### Running the Sugar News Test

```bash
# Test with real Sugar news articles from ClickHouse
python test_sugar_news_with_topics.py
```

## Database Schema

### news.prompts Table Schema

The `news.prompts` table has the following schema:

```sql
CREATE TABLE news.prompts (
    article_id String,
    system_prompt String,
    user_prompt String,
    response String,
    sentiment String,
    confidence Float32,
    reasoning String,
    title Nullable(String),
    commodity Nullable(String),
    topics Nullable(String),
    created_at DateTime
) ENGINE = MergeTree()
ORDER BY (article_id, created_at)
```

## Error Handling

The enhanced predictor includes comprehensive error handling:

1. **ClickHouse Connection Errors**: Gracefully handles connection issues and continues operation if ClickHouse is unavailable.
2. **Invalid Topics**: Handles None or empty topics gracefully.
3. **Metadata Parsing**: Safely parses metadata JSON with fallback for invalid formats.
4. **API Errors**: Maintains existing error handling for API calls and response parsing.

## Dependencies

The enhanced predictor requires the following additional dependencies:

- `clickhouse-driver`: For ClickHouse database connectivity
- `sugar.backend.config`: For ClickHouse configuration

These dependencies are optional and will only be imported when `save_prompts=True`.

## Migration Guide

### For Existing Code

Existing code using the predictor will continue to work without changes. The new parameters are optional and have default values.

### For New Features

To use the new features:

1. Add the `topics` parameter to `analyze_sentiment()` calls
2. Set `save_prompts=True` in the constructor to enable ClickHouse saving
3. Provide `article_id` when saving prompts to ClickHouse

## Performance Considerations

1. **ClickHouse Overhead**: Saving prompts to ClickHouse adds minimal overhead to each analysis call.
2. **Batch Processing**: Use `batch_analyze()` for processing multiple articles to improve efficiency.
3. **Connection Management**: The ClickHouse client uses lazy initialization and maintains a single connection.

## Troubleshooting

### Common Issues

1. **ClickHouse Connection Failed**:
   - Ensure ClickHouse is running and accessible
   - Check environment variables for ClickHouse configuration
   - Verify network connectivity

2. **Import Error for ClickHouse Dependencies**:
   - Install clickhouse-driver: `pip install clickhouse-driver`
   - Ensure the sugar.backend.config module is accessible

3. **Prompts Not Saved**:
   - Verify `save_prompts=True` is set in the constructor
   - Ensure `article_id` is provided when calling `analyze_sentiment()`
   - Check ClickHouse permissions for the news database

### Debug Mode

Enable debug output by setting the environment variable:

```bash
export DEBUG=1
```

This will provide additional logging for ClickHouse operations and prompt saving.
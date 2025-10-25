# Sugar News Fetching Pipeline - User Guide

## Overview

This guide provides instructions for running the updated sugar news fetching pipeline with all the recent improvements, including enhanced filtering logic, fixed deduplication, and updated sugar sources.

## What's New in the Updated Pipeline

### Key Improvements

1. **Enhanced Filtering Logic**: The pipeline now checks both title and text for sugar-related keywords, improving article coverage
2. **Fixed Deduplication**: Articles with the same content from different sources are now preserved, improving source diversity
3. **Updated Sugar Sources**: Added 20 sugar-specific trusted sources for better coverage
4. **Fixed SQL Syntax Error**: Resolved issues in the delete_sugar_news.py script
5. **Improved Resource Management**: Better handling of concurrent API requests to prevent resource exhaustion
6. **Weekly Date Ranges**: Changed from monthly to weekly API calls to reduce the number of articles per call
7. **Dynamic Quota Allocation**: Implemented intelligent quota distribution based on source reliability and category
8. **Checkpoint and Recovery System**: Added robust checkpointing to prevent data loss during long-running fetches

### Technical Changes

- **Filtering Logic**: Changed from restrictive AND logic to simplified OR logic for better recall
- **Deduplication**: Now considers source information when identifying duplicates
- **Source Synchronization**: Ensured consistency between sugar_news_fetcher.py and source_filter.py
- **Cycle Loop Fix**: Resolved infinite loop issues in the sugar_news_fetcher.py
- **Date Range Generation**: Now generates weekly intervals (Monday to Sunday) instead of monthly ranges
- **Quota Allocation**: Dynamic quota system that allocates articles based on source category weights and reliability scores
- **Batch Database Writing**: All articles are collected in memory and written to the database in a single batch at the end of the process
- **Checkpoint System**: Intermediate results are saved after each batch to enable recovery from failures

## Prerequisites

### Environment Setup

1. **Python Environment**: Make sure you're using the correct Python environment:
   ```bash
   cd ShinkaEvolve/shinka/examples/sugar
   source ../sugarenv/bin/activate  # or your specific environment
   ```

2. **Environment Variables**: Ensure the following environment variables are set in your `.env` file:
   ```bash
   OPOINT_API_KEY=your_opoint_api_key_here
   CLICKHOUSE_HOST=your_clickhouse_host
   CLICKHOUSE_PORT=8123
   CLICKHOUSE_NATIVE_PORT=9000
   CLICKHOUSE_USERNAME=your_username
   CLICKHOUSE_PASSWORD=your_password
   CLICKHOUSE_DATABASE=news
   ```

### Required Dependencies

The pipeline requires the following Python packages (should be installed in your environment):
- `pandas`
- `clickhouse-driver`
- `requests`
- `python-dotenv`
- `transformers` (for language normalization)
- `langdetect` (for language detection)
- `spacy` (for slang/synonym mapping)
- `symspellpy` (for typo correction)

### Optional Dependencies

The following package is optional but recommended for enhanced functionality:
- `psutil` (for memory monitoring) - The pipeline will run without this package, but memory monitoring features will be disabled. If you want to enable memory monitoring, install it with:
  ```bash
  pip install psutil
  ```

## Running the Sugar News Fetching Pipeline

### Basic Usage

To run the sugar news fetching pipeline with default settings:

```bash
cd ShinkaEvolve/shinka/examples/sugar/backend/parsers
python sugar_news_fetcher.py
```

### Advanced Usage with Parameters

The pipeline supports several command-line parameters for customization:

```bash
python sugar_news_fetcher.py [OPTIONS]
```

#### Available Options

- `--dry-run`: Print what would be done without executing (useful for testing)
- `--max-workers N`: Set maximum number of concurrent workers (default: 2)
- `--weeks-back N`: Set number of weeks back to fetch (default: 48, approx 12 months)
- `--max-articles N`: Set maximum articles per request (default: 1000)
- `--resume`: Resume from the last checkpoint if the process was interrupted
- `--checkpoint-dir PATH`: Specify a custom directory for storing checkpoint files (default: ./checkpoints)

#### Example Commands

1. **Dry Run** (to test without actually fetching):
   ```bash
   python sugar_news_fetcher.py --dry-run
   ```

2. **Fetch Last 12 Weeks with 3 Workers**:
   ```bash
   python sugar_news_fetcher.py --weeks-back 12 --max-workers 3
   ```

3. **Fetch with Custom Article Limit**:
   ```bash
   python sugar_news_fetcher.py --max-articles 2000
   ```

4. **Resume from Last Checkpoint** (if the process was interrupted):
   ```bash
   python sugar_news_fetcher.py --resume
   ```

5. **Fetch with Custom Checkpoint Directory**:
   ```bash
   python sugar_news_fetcher.py --checkpoint-dir /path/to/custom/checkpoints
   ```

### Understanding the Output

The pipeline provides detailed logging output:

1. **Progress Information**: Shows which week and topic is being processed
2. **Dynamic Quota Allocation**: Displays how articles are allocated among sources based on reliability and category
3. **Source Distribution**: Breakdown of articles from sugar vs. non-sugar sources
4. **Triage Filter Results**: Number of articles that passed/failed the sugar-specific filtering
5. **Checkpoint Information**: Shows when intermediate results are saved and loaded
6. **Final Statistics**: Overall summary of articles processed and saved, including weekly interval analysis

## New Features: Weekly Intervals and Dynamic Quota Allocation

### Weekly Date Ranges

The pipeline now uses weekly intervals instead of monthly ranges for more granular data collection:

#### Benefits of Weekly Intervals

1. **Reduced API Load**: Smaller, more frequent calls reduce the risk of API timeouts and rate limiting
2. **Better Data Freshness**: More frequent fetching ensures more up-to-date information
3. **Improved Resource Management**: Smaller data batches reduce memory usage and processing time
4. **Enhanced Error Recovery**: If one week fails, it doesn't affect the entire month's data

#### How Weekly Ranges Work

- Each interval starts on Monday at 00:00:00
- Each interval ends on Sunday at 23:59:59
- Intervals are processed in chronological order (oldest first)
- Default is 48 weeks (approximately 12 months)

Example output:
```
Starting sugar news fetch across 48 weeks
Generated 4 weekly date ranges:
  Week 1: 2025-09-29 to 2025-10-05
  Week 2: 2025-10-06 to 2025-10-12
  Week 3: 2025-10-13 to 2025-10-19
  Week 4: 2025-10-20 to 2025-10-26
```

### Dynamic Quota Allocation

The pipeline now implements intelligent quota distribution based on source reliability and category importance.

#### How Dynamic Quota Works

1. **Source Categorization**: Sources are grouped into categories with different priority weights:
   - Sugar Industry Publications (weight: 1.0) - Highest priority
   - Agricultural Commodity Sources (weight: 0.8) - High priority
   - Government Sources (weight: 0.7) - High priority
   - Trade Publications (weight: 0.5) - Medium priority

2. **Reliability Scoring**: Each source has a reliability score (0.0-1.0) based on historical performance

3. **Quota Calculation**: The final quota for each source is calculated as:
   ```
   Quota = (Category Weight × Reliability Score) × Total Available Articles
   ```

#### Benefits of Dynamic Quota Allocation

1. **Optimized Resource Usage**: High-value sources get more quota, maximizing the quality of fetched articles
2. **Adaptive Performance**: Sources with better historical performance receive higher allocation
3. **Balanced Coverage**: Ensures all sources get at least a minimum quota while prioritizing high-value ones
4. **Transparent Allocation**: Detailed logging shows exactly how quotas are distributed

Example output:
```
=== DYNAMIC QUOTA ALLOCATION ===
Allocating quotas for 20 sugar sources:
  - Sugar Producer (sugar_industry_publications): 15 articles (reliability: 0.95)
  - Food Processing (sugar_industry_publications): 14 articles (reliability: 0.90)
  - ICE (agricultural_commodity_sources): 11 articles (reliability: 0.95)
  - USDA (government_sources): 10 articles (reliability: 0.95)
  - Yahoo! Finance (trade_publications): 4 articles (reliability: 0.50)
Total sugar sources quota: 94 articles
```

#### Quota Utilization Tracking

The pipeline tracks how effectively each source uses its allocated quota:

```
=== SUGAR SOURCES PRIORITY ANALYSIS ===
  - Sugar Producer (sugar_industry_publications): 12 articles (80.0% passed triage)
    Allocated quota: 15, Utilization: 80.0%, Reliability: 0.95
  - Food Processing (sugar_industry_publications): 10 articles (70.0% passed triage)
    Allocated quota: 14, Utilization: 71.4%, Reliability: 0.90
```

### Configuration and Customization

#### Modifying Source Reliability Scores

To update source reliability scores based on observed performance:

1. Edit the `SOURCE_RELIABILITY_SCORES` dictionary in `sugar_news_fetcher.py`
2. Adjust scores between 0.0 (low reliability) and 1.0 (high reliability)
3. Higher scores result in larger quota allocations

#### Adjusting Category Weights

To change the priority of source categories:

1. Edit the `SOURCE_CATEGORY_WEIGHTS` dictionary in `sugar_news_fetcher.py`
2. Adjust weights based on your specific needs
3. Weights are relative - higher values get more quota

#### Adding New Sources

To add new sources to the dynamic quota system:

1. Add the source to the appropriate category in `SUGAR_SOURCES`
2. Assign a reliability score in `SOURCE_RELIABILITY_SCORES`
3. Ensure the source is also added to `source_filter.py` for consistency

Example output snippet:
```
=== DYNAMIC QUOTA ALLOCATION ===
Allocating quotas for 20 sugar sources:
  - Sugar Producer (sugar_industry_publications): 15 articles (reliability: 0.95)
  - Food Processing (sugar_industry_publications): 14 articles (reliability: 0.90)
  - ICE (agricultural_commodity_sources): 11 articles (reliability: 0.95)
  - USDA (government_sources): 10 articles (reliability: 0.95)
  - Yahoo! Finance (trade_publications): 4 articles (reliability: 0.50)
Total sugar sources quota: 94 articles

=== STEP 1: Fetching from sugar sources ===
Filtering for 20 sugar-specific sources with dynamic quotas
  Fetching from sugar_industry_publications: ['Food Processing', 'Sugar Producer']
    Found 12 articles from Food Processing (quota: 14)
    Found 10 articles from Sugar Producer (quota: 15)

=== STEP 2: Fetching from non-sugar sources ===
Allocating 50 articles for non-sugar sources
Found 35 articles from non-sugar sources (quota: 50)

=== STEP 4: Applying normalization and triage pipeline to all articles ===
Triage filter results for 2025-10-20:
  - Passed: 18 articles (asset='Sugar')
  - Failed: 39 articles (asset='General')
  - Total processed: 57 articles

=== SOURCE DISTRIBUTION ANALYSIS ===
Total articles: 57
  - Sugar sources: 32 articles
  - Non-sugar sources: 25 articles

=== SUGAR SOURCES PRIORITY ANALYSIS ===
  - Sugar Producer (sugar_industry_publications): 10 articles (80.0% passed triage)
    Allocated quota: 15, Utilization: 66.7%, Reliability: 0.95
  - Food Processing (sugar_industry_publications): 8 articles (75.0% passed triage)
    Allocated quota: 14, Utilization: 57.1%, Reliability: 0.90

Weekly interval analysis (2025-10-20 to 2025-10-26):
  - Articles per day: 4.6
  - High-value sources (pass rate > 70%): 2
```

## New Features: Batch Database Writing and Checkpoint System

### Batch Database Writing

The pipeline now uses a batch writing approach where all articles are collected in memory and written to the database in a single operation at the end of the process.

#### Benefits of Batch Writing

1. **Improved Performance**: Fewer database connections and transactions reduce overhead
2. **Better Deduplication**: All articles are deduplicated together, allowing for more effective duplicate detection across all periods
3. **Atomic Operations**: Either all articles are saved or none are, ensuring data consistency
4. **Reduced Database Load**: Minimizes the impact on the database system

#### How Batch Writing Works

1. **Collection Phase**: Articles from all periods are collected in memory
2. **Processing Phase**: All articles go through filtering and deduplication together
3. **Writing Phase**: All processed articles are saved to the database in a single batch operation

### Checkpoint and Recovery System

To address the risk of data loss with batch writing, the pipeline now includes a comprehensive checkpointing system that saves intermediate results during processing.

#### How Checkpointing Works

1. **Automatic Checkpoints**: After processing each batch of articles, intermediate results are automatically saved to disk
2. **Recovery Capability**: If the process is interrupted, it can be resumed from the last checkpoint
3. **Cleanup**: After successful completion, checkpoint files are automatically cleaned up

#### Checkpoint File Structure

```
checkpoints/
├── intermediate_results_batch_1_20251025_160505.pkl
├── intermediate_results_batch_2_20251025_160505.pkl
└── checkpoint_state.pkl
```

#### Using the Checkpoint System

1. **Normal Operation**: The pipeline automatically creates checkpoints during processing
2. **After Interruption**: Use the `--resume` flag to continue from the last checkpoint
3. **Custom Directory**: Use `--checkpoint-dir` to specify a custom location for checkpoint files

Example output with checkpoint information:
```
2025-10-25 16:05:05,083 - sugar.backend.parsers.sugar_news_fetcher - INFO - Intermediate results saved to ./checkpoints/intermediate_results_batch_1_20251025_160505.pkl
2025-10-25 16:05:05,084 - sugar.backend.parsers.sugar_news_fetcher - INFO - Checkpoint saved to ./checkpoints/checkpoint_state.pkl
2025-10-25 16:05:05,085 - sugar.backend.parsers.sugar_news_fetcher - INFO - Loaded intermediate results from intermediate_results_batch_1_20251025_160505.pkl
2025-10-25 16:05:05,086 - sugar.backend.parsers.sugar_news_fetcher - INFO - Removed empty checkpoint directory: ./checkpoints
```

#### Error Handling and Recovery

The checkpoint system includes robust error handling:

1. **Graceful Degradation**: If checkpoint saving fails, the pipeline continues with a warning
2. **Validation**: Checkpoint files are validated before use
3. **Cleanup**: Failed or corrupted checkpoint files are automatically cleaned up
4. **Global Exception Handling**: Ensures data is preserved even if the process crashes

#### Memory Considerations

With batch writing, all articles are kept in memory until the final save operation:

1. **Memory Monitoring**: The pipeline includes memory usage monitoring (if psutil is available)
2. **Batch Processing**: Large datasets are processed in smaller batches to manage memory usage
3. **Checkpoint Offloading**: Intermediate results can be offloaded to disk to reduce memory pressure

#### Testing the Checkpoint System

A test script is available to verify the checkpoint functionality:

```bash
cd ShinkaEvolve/shinka/examples/sugar/backend/scripts
python test_checkpoint_functionality.py
```

This script tests:
- Saving and loading intermediate results
- Checkpoint creation and restoration
- Error handling for various failure scenarios
- Cleanup of checkpoint files

## Managing Sugar News Data

### Deleting Existing Sugar News

If you need to clear existing sugar news data before running a fresh fetch:

1. **Dry Run First** (to see what would be deleted):
   ```bash
   cd ShinkaEvolve/shinka/examples/sugar/backend/scripts
   python delete_sugar_news.py
   ```

2. **Actual Deletion** (after confirming):
   ```bash
   python delete_sugar_news.py --execute
   ```

The delete script will:
- Show a preview of articles that would be deleted
- Ask for confirmation before proceeding
- Provide a summary of deletion results

### Verifying Data in Database

To check what sugar news data is currently in your database:

```sql
-- Count sugar articles
SELECT COUNT(*) as sugar_articles 
FROM news.news 
WHERE lower(asset) LIKE '%sugar%';

-- View recent sugar articles
SELECT id, datetime, source, title, asset 
FROM news.news 
WHERE lower(asset) LIKE '%sugar%'
ORDER BY datetime DESC 
LIMIT 10;
```

## Testing the Pipeline

### Running Test Scripts

The pipeline includes comprehensive test scripts to verify functionality:

1. **Test Sugar Sources Configuration**:
   ```bash
   cd ShinkaEvolve/shinka/examples/sugar/backend/scripts
   python test_sugar_sources.py
   ```

2. **Test Deduplication and Filtering**:
   ```bash
   python test_deduplication_filtering.py
   ```

Both tests should pass with "All tests PASSED!" if everything is working correctly.

### Expected Test Results

#### test_sugar_sources.py
- ✓ Source counts are consistent
- ✓ All sources are unique
- ✓ All source names are unique
- ✓ Source names and IDs counts match
- ✓ All sugar sources are trusted by name and ID
- ✓ Generic source filtering still works
- ✓ Sugar sources are properly included in search queries

#### test_deduplication_filtering.py
- ✓ Deduplication with source: PASSED
- ✓ Filtering with title and text: PASSED
- ✓ Backward compatibility: PASSED

## Troubleshooting

### Common Issues and Solutions

1. **API Key Not Found**:
   ```
   Error: OPOINT_API_KEY environment variable not found
   ```
   **Solution**: Ensure your `.env` file contains the OPOINT_API_KEY variable

2. **Database Connection Issues**:
   ```
   Error connecting to ClickHouse: Connection refused
   ```
   **Solution**: Verify your ClickHouse connection parameters in the `.env` file

3. **Resource Exhaustion**:
   ```
   Timeout waiting for available API request slot
   ```
   **Solution**: Reduce the `--max-workers` parameter (e.g., `--max-workers 3`)

4. **No Articles Found**:
   ```
   No articles found for sugar in [date]
   ```
   **Solution**: 
   - Check if your OPOINT API key is valid
   - Verify the date range is appropriate
   - Try with a shorter time period first

5. **Memory Issues**:
    ```
    Killed: 9
    ```
    **Solution**: Reduce `--max-articles` and `--months-back` parameters

6. **psutil Module Not Found**:
    ```
    Warning: psutil module not found. Memory monitoring will be disabled.
    ```
    **Solution**: This is a warning, not an error. The pipeline will continue to run without memory monitoring. If you want to enable memory monitoring features, install psutil:
    ```bash
    pip install psutil
    ```

### Performance Optimization

For optimal performance with the new weekly intervals and dynamic quota allocation:

1. **Concurrent Workers**: Start with `--max-workers 2` and increase gradually (weekly processing is less resource-intensive)
2. **Article Limits**: Use `--max-articles 1000` for initial testing (smaller batches due to weekly processing)
3. **Time Range**: Start with `--weeks-back 4` for testing, then increase to 48 weeks (12 months)
4. **Resource Monitoring**: Watch system resources during execution (weekly processing uses less memory)
5. **Quota Optimization**: Monitor quota utilization rates and adjust reliability scores accordingly
6. **Batch Processing**: The pipeline automatically processes tasks in batches to prevent resource exhaustion

### Debug Mode

For detailed debugging information, check the log file:
```bash
tail -f sugar_news_fetcher_debug.log
```

## Understanding the Pipeline Flow

### Step-by-Step Process

1. **Source Separation**: The pipeline fetches from sugar-specific and non-sugar sources separately
2. **API Requests**: Makes controlled API calls to avoid overwhelming the service
3. **Content Normalization**: Applies language normalization, typo correction, and slang mapping
4. **Triage Filtering**: Applies sugar-specific filtering logic to both title and text
5. **Deduplication**: Removes duplicates while preserving source diversity
6. **Source Filtering**: Ensures only trusted sources are included
7. **Database Storage**: Saves only articles that passed all filters

### Filtering Logic

The updated filtering logic works as follows:

1. **Quality Controls**: Checks for minimum length, valid content, etc.
2. **Main Keywords**: Looks for sugar-related terms in title OR text
3. **Exclusion Keywords**: Rejects articles with non-sugar commodity terms
4. **Context Zones**: Optionally checks for market, supply chain, event, or region keywords
5. **Structured Pricing**: Extracts pricing data if present

### Deduplication Logic

The enhanced deduplication:

1. **Content Hash**: Generates hash based on title, text, AND source
2. **Source Awareness**: Same content from different sources is NOT considered duplicate
3. **Similarity Check**: Uses Jaccard similarity for fuzzy matching within same source

## Best Practices

### For Regular Use

1. **Start Small**: Begin with limited week ranges (e.g., `--weeks-back 4`) and increase gradually
2. **Monitor Resources**: Keep an eye on system resources during execution (weekly processing is less intensive)
3. **Regular Updates**: Run the pipeline weekly for fresh data (now optimized for weekly intervals)
4. **Data Cleanup**: Periodically clean old data using the delete script
5. **Quota Monitoring**: Review quota utilization rates and adjust reliability scores for better performance

### For Production

1. **Schedule Runs**: Use cron jobs or similar for automated weekly execution
2. **Monitor Logs**: Set up log monitoring for error detection and quota utilization analysis
3. **Database Maintenance**: Regular database optimization and cleanup
4. **API Quotas**: Monitor API usage to avoid hitting limits (weekly calls are more predictable)
5. **Performance Tuning**: Regularly review and update source reliability scores based on actual performance
6. **Resource Planning**: Weekly processing allows for more predictable resource usage planning

## Support

If you encounter issues not covered in this guide:

1. Check the test scripts first - they can help identify configuration problems
2. Review the debug log file for detailed error information
3. Verify all environment variables are correctly set
4. Ensure all required dependencies are installed in your environment

## Conclusion

The updated sugar news fetching pipeline provides improved coverage, better source diversity, and more reliable filtering while maintaining backward compatibility. With the new weekly intervals and dynamic quota allocation system, the pipeline now offers:

1. **More Efficient API Usage**: Weekly intervals reduce the risk of timeouts and rate limiting
2. **Smarter Resource Allocation**: Dynamic quotas prioritize high-value sources based on reliability and category
3. **Better Data Freshness**: More frequent fetching ensures up-to-date information
4. **Enhanced Monitoring**: Detailed logging and statistics provide insights into source performance and quota utilization
5. **Flexible Configuration**: Easy to adjust source reliability scores and category weights based on observed performance

By following this guide, you should be able to successfully run the pipeline and fetch high-quality sugar news articles for your analysis needs with optimal efficiency and resource usage.
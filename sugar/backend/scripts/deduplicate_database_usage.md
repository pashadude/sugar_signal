# Database Deduplication Script Usage

## Overview

The `deduplicate_database.py` script is designed to remove duplicate articles from the ClickHouse `news.news` table where the asset is 'Sugar'. It identifies duplicates based on matching title, text, source, and date fields.

## Features

- Connects to ClickHouse database using existing configuration
- Only processes records where asset = 'Sugar'
- Identifies duplicates based on title, text, source, and date
- Provides dry-run mode to preview what would be removed
- Allows choosing to keep newest or oldest record when duplicates are found
- Processes data in batches for efficiency with large datasets
- Generates detailed reports of deduplication operations
- Verifies that duplicates have been successfully removed

## Usage

### Basic Dry Run (Recommended First)

```bash
python deduplicate_database.py --dry-run
```

This will show what duplicates would be removed without actually removing them.

### Execute Deduplication

```bash
python deduplicate_database.py --execute
```

This will actually remove the duplicate articles from the database.

### Keep Oldest Records

```bash
python deduplicate_database.py --execute --keep-oldest
```

This will keep the oldest record instead of the newest when duplicates are found.

### Custom Batch Size

```bash
python deduplicate_database.py --dry-run --batch-size 500
```

This processes 500 records at a time instead of the default 1000.

## Command Line Options

- `--dry-run`: Show what would be removed without actually removing (default: True)
- `--execute`: Actually remove duplicates (disables dry-run mode)
- `--keep-oldest`: Keep the oldest record instead of the newest when duplicates are found
- `--batch-size`: Number of records to process at once (default: 1000)

## Output

The script provides:

1. **Connection Status**: Shows successful connection to ClickHouse
2. **Progress Information**: Shows processing progress with batch information
3. **Duplicate Summary**: Shows total duplicate groups and articles to be removed
4. **Sample Duplicates**: Displays first 5 duplicate groups for review
5. **Final Summary**: Shows total duplicates found and removed
6. **Report File**: Generates a JSON report with detailed information

## Report File

The script creates a detailed JSON report file named `deduplication_report_YYYYMMDD_HHMMSS.json` containing:

- Timestamp of operation
- Total duplicate groups found
- Total duplicates found
- Number of duplicates removed
- Verification status
- Detailed information about each duplicate group

## Safety Features

1. **Dry Run Mode**: Always run in dry-run mode first to see what will be removed
2. **Batch Processing**: Processes data in manageable batches to avoid timeouts
3. **Verification**: After removal, verifies that duplicates were actually removed
4. **Detailed Logging**: Provides clear output of all operations performed

## Requirements

- Python 3.x
- ClickHouse driver (`clickhouse-driver`)
- Access to ClickHouse database with proper credentials
- .env file with database configuration

## Example Output

```
=== NEWS DATABASE DEDUPLICATION TOOL ===
Started at: 2025-10-27 21:37:00.640468
Mode: DRY RUN
Strategy: Keep newest record when duplicates found
Batch size: 100
✓ Successfully connected to ClickHouse database

Finding duplicate articles...
This may take a while for large datasets...
Total Sugar records in database: 12,558
Processing records 0 to 100...
Processing records 100 to 200...
Found 871 groups of duplicates
Total duplicate articles to be removed: 11,687

================================================================================
DUPLICATE ARTICLES FOUND
================================================================================
Total duplicate groups: 871
Total duplicate articles to be removed: 11687

Sample of duplicates (first 5 groups):

Group 1:
  Title: Year in review: A look at events in July 2024
  Source: Medicine Hat News
  Date: 2024-12-12 09:51:07
  Duplicate count: 26
  Keeping ID: 2f94c32c2e917d65da800d6c24f6e857 (created_at: 2025-10-27 17:11:29)
  Removing 25 duplicate(s):
    1. 2f94c32c2e917d65da800d6c24f6e857
    2. 2f94c32c2e917d65da800d6c24f6e857
    3. 2f94c32c2e917d65da800d6c24f6e857
    ... and 22 more

=== DRY RUN SUMMARY
================================================================================
Total duplicates found: 11687
Total duplicates that would be removed: 11687
Run with --execute to actually remove the duplicates
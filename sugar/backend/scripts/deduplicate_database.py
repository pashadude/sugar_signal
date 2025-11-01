#!/usr/bin/env python3
"""
Script to deduplicate Sugar news articles in the news.news database table by removing duplicates
that have the same title, text, source, and date. Only processes records where asset = 'Sugar'.
"""

import sys
import os
from pathlib import Path
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import configuration
try:
    from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
except ImportError:
    print("Error: Could not import ClickHouse configuration")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)

from clickhouse_driver import Client

def connect_to_clickhouse():
    """Connect to ClickHouse database"""
    try:
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        # Test connection
        client.execute("SELECT 1")
        print("✓ Successfully connected to ClickHouse database")
        return client
    except Exception as e:
        print(f"✗ Error connecting to ClickHouse: {e}")
        return None

def find_duplicates(client, keep_newest=True, batch_size=1000):
    """
    Find duplicate articles in the news.news table based on:
    - Same title
    - Same text
    - Same source
    - Same date (datetime field)
    
    Args:
        client: ClickHouse client
        keep_newest: If True, keep the newest record when duplicates are found
                    If False, keep the oldest record
        batch_size: Number of records to process at once
    
    Returns:
        List of duplicate groups and total count of duplicates
    """
    try:
        print("\nFinding duplicate articles...")
        print("This may take a while for large datasets...")
        
        # First, let's get a count of total records to process
        count_query = "SELECT COUNT(*) FROM news.news WHERE asset = 'Sugar'"
        total_records = client.execute(count_query)[0][0]
        print(f"Total Sugar records in database: {total_records:,}")
        
        # Query to find duplicates based on title, text, source, and datetime
        # Only for records where asset = 'Sugar'
        # Using a more efficient approach with LIMIT and OFFSET for pagination
        duplicate_groups = []
        total_duplicates = 0
        offset = 0
        
        while True:
            print(f"Processing records {offset:,} to {offset + batch_size:,}...")
            
            # Get a batch of potential duplicates
            batch_query = f"""
            SELECT
                title,
                text,
                source,
                datetime,
                COUNT(*) as duplicate_count,
                groupArray(id) as duplicate_ids,
                groupArray(created_at) as created_at_times
            FROM news.news
            WHERE asset = 'Sugar'
            GROUP BY
                title,
                text,
                source,
                datetime
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT {batch_size} OFFSET {offset}
            """
            
            batch_duplicates = client.execute(batch_query)
            
            if not batch_duplicates:
                break
            
            # Process this batch
            for title, text, source, datetime_val, count, ids, created_times in batch_duplicates:
                # Determine which record to keep based on created_at timestamp
                if keep_newest:
                    # Keep the record with the newest created_at timestamp
                    keep_index = created_times.index(max(created_times))
                else:
                    # Keep the record with the oldest created_at timestamp
                    keep_index = created_times.index(min(created_times))
                
                # The ID to keep
                keep_id = ids[keep_index]
                
                # IDs to remove (all except the one we're keeping)
                remove_ids = [id for i, id in enumerate(ids) if i != keep_index]
                
                duplicate_group = {
                    'title': title,
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'source': source,
                    'datetime': datetime_val,
                    'duplicate_count': count,
                    'keep_id': keep_id,
                    'remove_ids': remove_ids,
                    'keep_created_at': created_times[keep_index]
                }
                
                duplicate_groups.append(duplicate_group)
                total_duplicates += len(remove_ids)
            
            offset += batch_size
            
            # If we got fewer records than the batch size, we're done
            if len(batch_duplicates) < batch_size:
                break
        
        if not duplicate_groups:
            print("No duplicates found in the database.")
            return [], 0
        
        print(f"Found {len(duplicate_groups)} groups of duplicates")
        print(f"Total duplicate articles to be removed: {total_duplicates:,}")
        
        return duplicate_groups, total_duplicates
        
    except Exception as e:
        print(f"Error finding duplicates: {e}")
        return [], 0

def display_duplicates(duplicate_groups, total_duplicates):
    """Display the duplicates that will be removed"""
    print("\n" + "="*80)
    print("DUPLICATE ARTICLES FOUND")
    print("="*80)
    
    print(f"Total duplicate groups: {len(duplicate_groups)}")
    print(f"Total duplicate articles to be removed: {total_duplicates}")
    
    print("\nSample of duplicates (first 5 groups):")
    for i, group in enumerate(duplicate_groups[:5], 1):
        print(f"\nGroup {i}:")
        print(f"  Title: {group['title']}")
        print(f"  Source: {group['source']}")
        print(f"  Date: {group['datetime']}")
        print(f"  Duplicate count: {group['duplicate_count']}")
        print(f"  Keeping ID: {group['keep_id']} (created_at: {group['keep_created_at']})")
        print(f"  Removing {len(group['remove_ids'])} duplicate(s):")
        for j, remove_id in enumerate(group['remove_ids'][:3], 1):  # Show first 3
            print(f"    {j}. {remove_id}")
        if len(group['remove_ids']) > 3:
            print(f"    ... and {len(group['remove_ids']) - 3} more")
    
    if len(duplicate_groups) > 5:
        print(f"\n... and {len(duplicate_groups) - 5} more duplicate groups")

def remove_duplicates(client, duplicate_groups, dry_run=True):
    """
    Remove duplicate articles from the database
    
    Args:
        client: ClickHouse client
        duplicate_groups: List of duplicate groups
        dry_run: If True, only show what would be removed
    
    Returns:
        Number of articles removed
    """
    try:
        if dry_run:
            print("\n=== DRY RUN MODE ===")
            print("No articles will be removed. This is a preview only.")
            return 0
        
        print("\nRemoving duplicate articles...")
        
        total_removed = 0
        
        for group in duplicate_groups:
            remove_ids = group['remove_ids']
            
            if not remove_ids:
                continue
            
            # Build the DELETE query for this group
            ids_str = "', '".join(remove_ids)
            delete_query = f"""
            ALTER TABLE news.news
            DELETE WHERE id IN ('{ids_str}')
            """
            
            try:
                result = client.execute(delete_query)
                removed_count = len(remove_ids)
                total_removed += removed_count
                print(f"Removed {removed_count} duplicates for article: {group['title'][:50]}...")
            except Exception as e:
                print(f"Error removing duplicates for article {group['title'][:50]}...: {e}")
                continue
        
        return total_removed
        
    except Exception as e:
        print(f"Error removing duplicates: {e}")
        return 0

def verify_deduplication(client, duplicate_groups):
    """Verify that duplicates have been removed"""
    try:
        print("\nVerifying deduplication...")
        
        # Check if any of the duplicate IDs still exist
        all_remove_ids = []
        for group in duplicate_groups:
            all_remove_ids.extend(group['remove_ids'])
        
        if not all_remove_ids:
            print("No duplicates to verify")
            return True
        
        # Check in batches to avoid query size limits
        batch_size = 100
        remaining_ids = []
        
        for i in range(0, len(all_remove_ids), batch_size):
            batch_ids = all_remove_ids[i:i + batch_size]
            ids_str = "', '".join(batch_ids)
            
            query = f"""
            SELECT COUNT(*) 
            FROM news.news 
            WHERE id IN ('{ids_str}')
            """
            
            result = client.execute(query)
            count = result[0][0] if result else 0
            
            if count > 0:
                # Find which IDs still exist
                existing_query = f"""
                SELECT id 
                FROM news.news 
                WHERE id IN ('{ids_str}')
                """
                existing_ids = client.execute(existing_query)
                remaining_ids.extend([id[0] for id in existing_ids])
        
        if remaining_ids:
            print(f"⚠ Warning: {len(remaining_ids)} duplicate articles still exist in the database")
            return False
        else:
            print("✓ All duplicates successfully removed")
            return True
            
    except Exception as e:
        print(f"Error verifying deduplication: {e}")
        return False

def save_report(duplicate_groups, total_duplicates, removed_count, verification_passed):
    """Save a report of the deduplication process"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"deduplication_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duplicate_groups": len(duplicate_groups),
            "total_duplicates_found": total_duplicates,
            "duplicates_removed": removed_count,
            "verification_passed": verification_passed,
            "duplicate_groups": duplicate_groups
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"Error saving report: {e}")

def main():
    """Main function"""
    print("=== NEWS DATABASE DEDUPLICATION TOOL ===")
    print(f"Started at: {datetime.now()}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Deduplicate Sugar news articles in ClickHouse database')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Show what would be removed without actually removing (default: True)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually remove duplicates (disables dry-run mode)')
    parser.add_argument('--keep-oldest', action='store_true',
                       help='Keep the oldest record instead of the newest when duplicates are found')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Number of records to process at once (default: 1000)')
    
    args = parser.parse_args()
    
    # Set dry_run mode
    dry_run = not args.execute
    
    # Set which record to keep
    keep_newest = not args.keep_oldest
    
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print(f"Strategy: Keep {'newest' if keep_newest else 'oldest'} record when duplicates found")
    print(f"Batch size: {args.batch_size}")
    
    # Connect to database
    client = connect_to_clickhouse()
    if not client:
        sys.exit(1)
    
    try:
        # Find duplicates
        duplicate_groups, total_duplicates = find_duplicates(client, keep_newest=keep_newest, batch_size=args.batch_size)
        
        if not duplicate_groups:
            print("No duplicates found. Nothing to do.")
            return
        
        # Display duplicates
        display_duplicates(duplicate_groups, total_duplicates)
        
        # Remove duplicates
        removed_count = remove_duplicates(client, duplicate_groups, dry_run=dry_run)
        
        if not dry_run and removed_count > 0:
            # Verify removal
            verification_passed = verify_deduplication(client, duplicate_groups)
            
            # Print summary
            print("\n" + "="*80)
            print("DEDUPLICATION SUMMARY")
            print("="*80)
            print(f"Total duplicates found: {total_duplicates}")
            print(f"Total duplicates removed: {removed_count}")
            print(f"Verification: {'PASSED' if verification_passed else 'FAILED'}")
            
            # Save report
            save_report(duplicate_groups, total_duplicates, removed_count, verification_passed)
        elif dry_run:
            print("\n" + "="*80)
            print("DRY RUN SUMMARY")
            print("="*80)
            print(f"Total duplicates found: {total_duplicates}")
            print(f"Total duplicates that would be removed: {total_duplicates}")
            print("Run with --execute to actually remove the duplicates")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()
        print("\nDisconnected from ClickHouse database")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script for the database connection and data storage functionality
Tests ClickHouse connectivity, table operations, and data storage/retrieval
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import pandas as pd
import hashlib

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to ShinkaEvolve root
sys.path.insert(0, str(project_root))

def test_database_connection():
    """Test ClickHouse database connection"""
    print("Testing ClickHouse database connection...")
    
    try:
        from sugar.backend.config import CLICKHOUSE_NATIVE_CONFIG
        from clickhouse_driver import Client
        
        print(f"Attempting to connect to ClickHouse at {CLICKHOUSE_NATIVE_CONFIG['host']}:{CLICKHOUSE_NATIVE_CONFIG['port']}")
        
        # Test connection
        client = Client(**CLICKHOUSE_NATIVE_CONFIG)
        
        # Execute a simple query to test connectivity
        result = client.execute('SELECT 1 as test')
        
        if result and result[0][0] == 1:
            print("✓ ClickHouse connection successful")
            return True, client, None
        else:
            print("✗ ClickHouse connection failed - unexpected result")
            return False, None, "Unexpected query result"
            
    except Exception as e:
        print(f"✗ ClickHouse connection failed: {e}")
        return False, None, str(e)

def test_database_tables(client):
    """Test if required database tables exist"""
    print("\nTesting database tables...")
    
    try:
        # Check if news.news table exists
        tables = client.execute("SHOW TABLES FROM news")
        table_names = [table[0] for table in tables]
        
        print(f"Available tables: {table_names}")
        
        required_tables = ['news']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            print(f"✗ Missing required tables: {missing_tables}")
            return False, missing_tables
        else:
            print("✓ All required tables exist")
            return True, []
            
    except Exception as e:
        print(f"✗ Error checking tables: {e}")
        return False, [str(e)]

def test_table_schema(client):
    """Test if news table has the expected schema"""
    print("\nTesting table schema...")
    
    try:
        # Get table schema
        schema = client.execute("DESCRIBE TABLE news.news")
        
        print("Table schema:")
        for column in schema:
            print(f"  {column[0]}: {column[1]}")
        
        # Check for required columns
        required_columns = {
            'id': 'String',
            'datetime': 'DateTime',
            'source': 'String',
            'title': 'String',
            'text': 'String',
            'metadata': 'String',
            'created_at': 'DateTime',
            'asset': 'String'
        }
        
        schema_dict = {column[0]: column[1] for column in schema}
        missing_columns = []
        type_mismatches = []
        
        for col_name, expected_type in required_columns.items():
            if col_name not in schema_dict:
                missing_columns.append(col_name)
            elif expected_type not in schema_dict[col_name]:
                type_mismatches.append(f"{col_name}: expected {expected_type}, got {schema_dict[col_name]}")
        
        if missing_columns:
            print(f"✗ Missing columns: {missing_columns}")
            return False, {"missing": missing_columns, "type_mismatches": type_mismatches}
        
        if type_mismatches:
            print(f"✗ Type mismatches: {type_mismatches}")
            return False, {"missing": missing_columns, "type_mismatches": type_mismatches}
        
        print("✓ Table schema is correct")
        return True, {}
        
    except Exception as e:
        print(f"✗ Error checking schema: {e}")
        return False, {"error": str(e)}

def generate_test_article_id(index):
    """Generate a test article ID"""
    content = f"https://test.com/article{index}_Test Title_{datetime.now().strftime('%Y-%m-%d')}_Sugar"
    return hashlib.md5(content.encode()).hexdigest()

def test_data_insertion(client):
    """Test data insertion into the news table"""
    print("\nTesting data insertion...")
    
    try:
        # Create test data
        test_articles = []
        current_time = datetime.now()
        
        for i in range(3):
            article_id = generate_test_article_id(i)
            pub_date = current_time - timedelta(hours=i)
            
            article = (
                article_id,
                pub_date,
                f"Test Source {i+1}",
                f"Test Article Title {i+1}",
                f"This is test article content number {i+1} for database testing.",
                json.dumps({
                    "test_metadata": f"test_value_{i}",
                    "insertion_time": current_time.isoformat(),
                    "test_index": i
                }),
                "Sugar"
            )
            test_articles.append(article)
        
        # Insert test data (created_at has default value, so we don't specify it)
        print(f"Inserting {len(test_articles)} test articles...")
        result = client.execute(
            'INSERT INTO news.news (id, datetime, source, title, text, metadata, asset) VALUES',
            test_articles
        )
        
        print(f"✓ Insertion successful, affected rows: {result}")
        return True, test_articles
        
    except Exception as e:
        print(f"✗ Error inserting data: {e}")
        return False, []

def test_data_retrieval(client, test_articles):
    """Test data retrieval from the news table"""
    print("\nTesting data retrieval...")
    
    try:
        # Retrieve the test articles we just inserted
        test_ids = [article[0] for article in test_articles]
        
        print(f"Test article IDs: {test_ids}")
        
        # Build query to retrieve test articles
        id_list = "', '".join(test_ids)
        query = f"SELECT id, datetime, source, title, text, metadata, created_at, asset FROM news.news WHERE id IN ('{id_list}') ORDER BY datetime"
        
        retrieved_articles = client.execute(query)
        
        print(f"Retrieved {len(retrieved_articles)} articles")
        print(f"Retrieved article IDs: {[article[0] for article in retrieved_articles]}")
        
        if len(retrieved_articles) != len(test_articles):
            print(f"✗ Expected {len(test_articles)} articles, got {len(retrieved_articles)}")
            return False, []
        
        # Create a mapping of ID to article for easier comparison
        inserted_map = {article[0]: article for article in test_articles}
        retrieved_map = {article[0]: article for article in retrieved_articles}
        
        # Verify the data by matching IDs
        for article_id in test_ids:
            if article_id not in retrieved_map:
                print(f"✗ Article with ID {article_id} not found in retrieved articles")
                return False, []
            
            inserted = inserted_map[article_id]
            retrieved = retrieved_map[article_id]
            
            inserted_id, inserted_dt, inserted_source, inserted_title, inserted_text, inserted_meta, inserted_asset = inserted
            retrieved_id, retrieved_dt, retrieved_source, retrieved_title, retrieved_text, retrieved_meta, retrieved_created, retrieved_asset = retrieved
            
            # Check basic fields
            if inserted_id != retrieved_id:
                print(f"✗ ID mismatch: expected {inserted_id}, got {retrieved_id}")
                return False, []
            
            if inserted_source != retrieved_source:
                print(f"✗ Source mismatch for ID {article_id}: expected {inserted_source}, got {retrieved_source}")
                return False, []
            
            if inserted_title != retrieved_title:
                print(f"✗ Title mismatch for ID {article_id}: expected {inserted_title}, got {retrieved_title}")
                return False, []
            
            if inserted_text != retrieved_text:
                print(f"✗ Text mismatch for ID {article_id}: expected {inserted_text}, got {retrieved_text}")
                return False, []
            
            if inserted_asset != retrieved_asset:
                print(f"✗ Asset mismatch for ID {article_id}: expected {inserted_asset}, got {retrieved_asset}")
                return False, []
            
            # Check that created_at was set by the database
            if not retrieved_created:
                print(f"✗ created_at not set for article {article_id}")
                return False, []
        
        print("✓ All retrieved articles match inserted data")
        return True, retrieved_articles
        
    except Exception as e:
        print(f"✗ Error retrieving data: {e}")
        return False, []

def test_data_cleanup(client, test_articles):
    """Clean up test data"""
    print("\nCleaning up test data...")
    
    try:
        test_ids = [article[0] for article in test_articles]
        id_list = "', '".join(test_ids)
        
        # Delete test articles
        delete_query = f"DELETE FROM news.news WHERE id IN ('{id_list}')"
        result = client.execute(delete_query)
        
        print(f"✓ Cleaned up {result} test articles")
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning up data: {e}")
        return False

def test_duplicate_handling(client):
    """Test handling of duplicate articles"""
    print("\nTesting duplicate handling...")
    
    try:
        # Create a test article with specific ID
        article_id = generate_test_article_id(999)
        current_time = datetime.now()
        
        test_article = (
            article_id,
            current_time,
            "Duplicate Test Source",
            "Duplicate Test Title",
            "This is a test article for duplicate handling.",
            json.dumps({"test": "duplicate"}),
            "Sugar"
        )
        
        # Insert the article twice
        print("Inserting article first time...")
        result1 = client.execute(
            'INSERT INTO news.news (id, datetime, source, title, text, metadata, asset) VALUES',
            [test_article]
        )
        
        print("Inserting article second time...")
        result2 = client.execute(
            'INSERT INTO news.news (id, datetime, source, title, text, metadata, asset) VALUES',
            [test_article]
        )
        
        # Check how many articles exist
        count_query = f"SELECT COUNT(*) FROM news.news WHERE id = '{article_id}'"
        count_result = client.execute(count_query)
        article_count = count_result[0][0]
        
        print(f"Article count after duplicate insertion: {article_count}")
        
        # Clean up
        client.execute(f"DELETE FROM news.news WHERE id = '{article_id}'")
        
        # ClickHouse allows duplicates by design (no unique constraint), so we expect 2 articles
        if article_count == 2:
            print("✓ Duplicate handling working as expected (ClickHouse allows duplicates by design)")
            return True
        else:
            print(f"✗ Unexpected duplicate handling: expected 2 articles, found {article_count}")
            return False
        
    except Exception as e:
        print(f"✗ Error testing duplicate handling: {e}")
        return False

def main():
    """Main test function"""
    print("=== DATABASE TEST SUITE ===")
    print(f"Started at: {datetime.now()}")
    
    # Track overall results
    all_passed = True
    test_results = []
    
    # Test 1: Database Connection
    conn_passed, client, conn_error = test_database_connection()
    test_results.append({
        "test": "Database Connection",
        "passed": conn_passed,
        "error": conn_error if not conn_passed else None
    })
    all_passed = all_passed and conn_passed
    
    if not conn_passed:
        print("\n=== DATABASE TEST RESULTS ===")
        print("Database connection failed. Skipping remaining tests.")
        print(f"Overall: FAILED")
        return 1
    
    # Test 2: Database Tables
    tables_passed, missing_tables = test_database_tables(client)
    test_results.append({
        "test": "Database Tables",
        "passed": tables_passed,
        "missing_tables": missing_tables if not tables_passed else None
    })
    all_passed = all_passed and tables_passed
    
    # Test 3: Table Schema
    schema_passed, schema_issues = test_table_schema(client)
    test_results.append({
        "test": "Table Schema",
        "passed": schema_passed,
        "issues": schema_issues if not schema_passed else None
    })
    all_passed = all_passed and schema_passed
    
    # Test 4: Data Insertion
    insert_passed, test_articles = test_data_insertion(client)
    test_results.append({
        "test": "Data Insertion",
        "passed": insert_passed,
        "articles_inserted": len(test_articles) if insert_passed else 0
    })
    all_passed = all_passed and insert_passed
    
    # Test 5: Data Retrieval
    if insert_passed:
        retrieve_passed, retrieved_articles = test_data_retrieval(client, test_articles)
        test_results.append({
            "test": "Data Retrieval",
            "passed": retrieve_passed,
            "articles_retrieved": len(retrieved_articles) if retrieve_passed else 0
        })
        all_passed = all_passed and retrieve_passed
    else:
        test_results.append({
            "test": "Data Retrieval",
            "passed": False,
            "skipped": True,
            "reason": "Depends on successful data insertion"
        })
        all_passed = False
    
    # Test 6: Duplicate Handling
    dup_passed = test_duplicate_handling(client)
    test_results.append({
        "test": "Duplicate Handling",
        "passed": dup_passed
    })
    all_passed = all_passed and dup_passed
    
    # Clean up test data if insertion was successful
    if insert_passed and test_articles:
        cleanup_passed = test_data_cleanup(client, test_articles)
        test_results.append({
            "test": "Data Cleanup",
            "passed": cleanup_passed
        })
    
    # Close connection
    try:
        client.disconnect()
        print("✓ Database connection closed")
    except:
        pass
    
    # Print results
    print(f"\n=== DATABASE TEST RESULTS ===")
    for result in test_results:
        status = "PASSED" if result["passed"] else "FAILED"
        print(f"{result['test']}: {status}")
        if not result["passed"] and "error" in result:
            print(f"  Error: {result['error']}")
        if not result["passed"] and "missing_tables" in result:
            print(f"  Missing tables: {result['missing_tables']}")
        if not result["passed"] and "issues" in result:
            print(f"  Issues: {result['issues']}")
    
    print(f"Overall: {'PASSED' if all_passed else 'FAILED'}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"database_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"Detailed results saved to: {results_file}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
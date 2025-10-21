#!/usr/bin/env python
"""
Script to verify the data in the news.source_of_truth table.
"""
import os
from dotenv import load_dotenv
from clickhouse_driver import Client

def main():
    # Load environment variables
    load_dotenv()

    # Get ClickHouse credentials
    clickhouse_host = os.getenv('CLICKHOUSE_HOST')
    clickhouse_user = os.getenv('CLICKHOUSE_USERNAME')
    clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')

    if not all([clickhouse_host, clickhouse_user, clickhouse_password]):
        raise ValueError("Missing required ClickHouse credentials in .env file")

    try:
        # Connect to ClickHouse
        client = Client(
            host=clickhouse_host,
            port=9000,
            user=clickhouse_user,
            password=clickhouse_password
        )

        print("Connected to ClickHouse. Running verification queries...\n")

        # 1. Get total count
        count = client.execute("SELECT count() FROM news.source_of_truth")[0][0]
        print(f"Total rows in table: {count}")

        # 2. Get sample row
        print("\nSample row:")
        sample = client.execute("SELECT * FROM news.source_of_truth LIMIT 1")
        if sample:
            row = sample[0]
            print(f"Sample row tuple length: {len(row)}")
            print(f"Sample row contents: {row}")
            # The following lines are commented out for diagnosis
            # print(f"ID: {row[0]}")
            # print(f"Timestamp Created: {row[1]}")
            # print(f"Timestamp Added: {row[2]}")
            # print(f"Commodity: {row[3]}")
            # print(f"Sentiment: {row[4]}")
            # print(f"Confidence: {row[5]}")
            # print(f"Source: {row[6]}")
            # print(f"Events: {row[7]}")
            # print(f"Prob Pos: {row[8]}")
            # print(f"Prob Neg: {row[9]}")
            # print(f"Prob Neu: {row[10]}")

        # 3. Get commodity distribution
        print("\nCommodity distribution (top 10):")
        commodities = client.execute("""
            SELECT commodity, count() as count 
            FROM news.source_of_truth 
            GROUP BY commodity 
            ORDER BY count DESC 
            LIMIT 10
        """)
        for commodity, count in commodities:
            print(f"{commodity}: {count} records")

        # 4. Get sentiment distribution
        print("\nSentiment distribution:")
        sentiments = client.execute("""
            SELECT sentiment, count() as count 
            FROM news.source_of_truth 
            GROUP BY sentiment 
            ORDER BY count DESC
        """)
        for sentiment, count in sentiments:
            print(f"{sentiment}: {count} records")

        # 5. Get date range
        print("\nDate range:")
        dates = client.execute("""
            SELECT 
                min(timestamp_created) as min_date,
                max(timestamp_created) as max_date 
            FROM news.source_of_truth
        """)[0]
        print(f"From: {dates[0]}")
        print(f"To: {dates[1]}")

        # 6. Get average confidence by sentiment
        print("\nAverage confidence by sentiment:")
        confidences = client.execute("""
            SELECT 
                sentiment,
                round(avg(confidence), 3) as avg_confidence,
                count() as count
            FROM news.source_of_truth 
            GROUP BY sentiment 
            ORDER BY avg_confidence DESC
        """)
        for sentiment, avg_conf, count in confidences:
            print(f"{sentiment}: {avg_conf} (based on {count} records)")

        # 7. Text/title population stats
        print("\nText/title population stats:")
        text_count = client.execute("SELECT count() FROM news.source_of_truth WHERE text != ''")[0][0]
        title_count = client.execute("SELECT count() FROM news.source_of_truth WHERE title != ''")[0][0]
        total_count = client.execute("SELECT count() FROM news.source_of_truth")[0][0]
        print(f"Rows with non-empty text: {text_count} ({text_count/total_count:.2%})")
        print(f"Rows with non-empty title: {title_count} ({title_count/total_count:.2%})")

        # 8. Sample populated text/title
        print("\nSample populated text/title rows:")
        samples = client.execute("SELECT timestamp_created, commodity, text, title FROM news.source_of_truth WHERE text != '' AND title != '' LIMIT 5")
        for row in samples:
            print(f"Timestamp: {row[0]}, Commodity: {row[1]}\nTitle: {row[3]}\nText: {row[2]}\n---")

        # 9. Top 10 popular titles
        print("\nTop 10 most frequent titles:")
        top_titles = client.execute("""
            SELECT title, count() as cnt
            FROM news.source_of_truth
            WHERE title != ''
            GROUP BY title
            ORDER BY cnt DESC
            LIMIT 10
        """)
        for idx, (title, cnt) in enumerate(top_titles, 1):
            print(f"{idx}. {title} ({cnt} occurrences)")

        # 10. Sample of timestamp_created, commodity, source for 2025 records
        print("\nSample of timestamp_created, commodity, source from DB (2025 records):")
        db_samples_2025 = client.execute("""
            SELECT timestamp_created, commodity, source
            FROM news.source_of_truth
            WHERE toYear(timestamp_created) = 2025
            LIMIT 10
        """)
        for row in db_samples_2025:
            print(f"timestamp_created: {row[0]}, commodity: {row[1]}, source: {row[2]}")

        # 11. Unique source values and their counts for 2025 records
        print("\nUnique source values and their counts for 2025 records:")
        sources_2025 = client.execute("""
            SELECT source, count() as cnt
            FROM news.source_of_truth
            WHERE toYear(timestamp_created) = 2025
            GROUP BY source
            ORDER BY cnt DESC
        """)
        for source, cnt in sources_2025:
            print(f"{source}: {cnt}")

    except Exception as e:
        print(f"Error verifying data: {str(e)}")
        raise

if __name__ == '__main__':
    main() 
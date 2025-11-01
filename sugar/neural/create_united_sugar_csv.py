import pandas as pd
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

def load_env():
    """Load environment variables"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(env_path)

def create_united_sugar_csv():
    """Create united CSV with all data sources without matching"""
    
    print("=== Creating United Sugar Dataset ===")
    
    # 1. Read predictions CSV
    print("1. Reading predictions CSV...")
    predictions_df = pd.read_csv('sugar_complete_dataset_with_predictions.csv')
    predictions_df['datetime'] = pd.to_datetime(predictions_df['datetime'])
    
    # Create sentiment numeric column (-1, 0, 1) for predictions
    sentiment_map = {'negative': -1, 'neutral': 0, 'positive': 1}
    predictions_df['sentiment_numeric'] = predictions_df['sentiment'].map(sentiment_map)
    
    # Create confidence column based on sentiment for predictions
    def get_confidence(row):
        if row['sentiment'] == 'negative':
            return row['prob_negative']
        elif row['sentiment'] == 'neutral':
            return row['prob_neutral']
        elif row['sentiment'] == 'positive':
            return row['prob_positive']
        else:
            return np.nan
    
    predictions_df['confidence'] = predictions_df.apply(get_confidence, axis=1)
    
    # Create predictions dataframe with required columns
    pred_data = pd.DataFrame()
    pred_data['datetime'] = predictions_df['datetime']
    pred_data['sentiment'] = predictions_df['sentiment_numeric']
    pred_data['confidence'] = predictions_df['confidence']
    pred_data['source'] = 'prediction'
    pred_data['title'] = predictions_df['title']
    
    # 2. Read source of truth CSV
    print("2. Reading source of truth CSV...")
    source_df = pd.read_csv('source_of_truth_sugar.csv')
    source_df['timestamp_created'] = pd.to_datetime(source_df['timestamp_created'])
    
    # Create source of truth dataframe with required columns
    source_data = pd.DataFrame()
    source_data['datetime'] = source_df['timestamp_created']
    source_data['sentiment'] = source_df['sentiment']
    source_data['confidence'] = source_df['confidence']
    source_data['source'] = 'source_of_truth'
    source_data['title'] = source_df['title']
    
    # 3. Get data from database
    print("3. Getting data from database...")
    try:
        from clickhouse_driver import Client
        
        load_env()
        
        ch_host = os.getenv('CLICKHOUSE_HOST', 'localhost')
        ch_port = int(os.getenv('CLICKHOUSE_PORT', 9000))
        ch_user = os.getenv('CLICKHOUSE_USER', 'default')
        ch_password = os.getenv('CLICKHOUSE_PASSWORD', '')
        ch_database = os.getenv('CLICKHOUSE_DATABASE', 'news')
        
        client = Client(
            host=ch_host,
            port=ch_port,
            user=ch_user,
            password=ch_password,
            database=ch_database
        )
        
        # Get sugar articles with sentiment predictions from database
        query = """
        SELECT 
            n.datetime,
            sp.sentiment,
            CASE 
                WHEN sp.sentiment = 'negative' THEN sp.prob_negative
                WHEN sp.sentiment = 'neutral' THEN sp.prob_neutral
                WHEN sp.sentiment = 'positive' THEN sp.prob_positive
                ELSE NULL
            END as confidence,
            n.title,
            'database' as source
        FROM news.news n
        LEFT JOIN sentiment_predictions sp ON n.id = sp.news_id
        WHERE n.asset = 'Sugar'
        AND n.datetime >= '2021-01-01'
        AND n.datetime <= '2025-05-31'
        ORDER BY n.datetime
        """
        
        result = client.execute(query)
        columns = ['datetime', 'sentiment', 'confidence', 'title', 'source']
        db_data = pd.DataFrame(result, columns=columns)
        
        # Convert datetime and sentiment
        db_data['datetime'] = pd.to_datetime(db_data['datetime'])
        db_data['sentiment'] = db_data['sentiment'].map(sentiment_map)
        
        print(f"   Retrieved {len(db_data)} articles from database")
        
    except Exception as e:
        print(f"   Error connecting to database: {e}")
        db_data = pd.DataFrame()
    
    # 4. Combine all data sources
    print("4. Combining all data sources...")
    
    # List of all dataframes
    all_data = []
    
    if not pred_data.empty:
        all_data.append(pred_data)
        print(f"   Added {len(pred_data)} prediction records")
    
    if not source_data.empty:
        all_data.append(source_data)
        print(f"   Added {len(source_data)} source of truth records")
    
    if not db_data.empty:
        all_data.append(db_data)
        print(f"   Added {len(db_data)} database records")
    
    # Concatenate all data
    if all_data:
        united_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by datetime
        united_df = united_df.sort_values('datetime')
        
        # Reset index
        united_df = united_df.reset_index(drop=True)
        
        # 5. Save to CSV
        output_file = 'sugar_united_dataset.csv'
        united_df.to_csv(output_file, index=False)
        
        # 6. Print statistics
        print(f"\n=== United Dataset Statistics ===")
        print(f"Total records: {len(united_df)}")
        print(f"Date range: {united_df['datetime'].min()} to {united_df['datetime'].max()}")
        
        print(f"\nRecords by source:")
        print(united_df['source'].value_counts())
        
        print(f"\nOverall sentiment distribution:")
        print(united_df['sentiment'].value_counts().sort_index())
        
        print(f"\nSentiment distribution by source:")
        for source in united_df['source'].unique():
            source_subset = united_df[united_df['source'] == source]
            print(f"\n{source}:")
            print(source_subset['sentiment'].value_counts().sort_index())
        
        print(f"\nUnited CSV saved to: {output_file}")
        
        return united_df
    else:
        print("No data to combine!")
        return pd.DataFrame()

if __name__ == "__main__":
    create_united_sugar_csv()
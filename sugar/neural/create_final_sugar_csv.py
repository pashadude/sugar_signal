import pandas as pd
import numpy as np
from datetime import datetime

def create_final_sugar_csv():
    """Create final CSV with specified columns and format"""
    
    # Read the predictions CSV
    print("Reading predictions CSV...")
    predictions_df = pd.read_csv('sugar_complete_dataset_with_predictions.csv')
    
    # Read the source of truth CSV
    print("Reading source of truth CSV...")
    source_df = pd.read_csv('source_of_truth_sugar.csv')
    
    # Convert datetime columns
    predictions_df['datetime'] = pd.to_datetime(predictions_df['datetime'])
    source_df['timestamp_created'] = pd.to_datetime(source_df['timestamp_created'])
    
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
    
    # Create final dataframe with required columns from predictions
    final_df = pd.DataFrame()
    final_df['datetime'] = predictions_df['datetime']
    final_df['sentiment'] = predictions_df['sentiment_numeric']
    final_df['confidence'] = predictions_df['confidence']
    
    # Add source_of_truth columns
    final_df['source_of_truth_datetime'] = np.nan
    final_df['source_of_truth_sentiment'] = np.nan
    final_df['source_of_truth_confidence'] = np.nan
    
    # Mark Dow Jones articles (all source of truth articles are Dow Jones)
    final_df['is_dow_jones'] = False
    
    # For each article in predictions, try to find matching source of truth data
    # We'll match by title similarity and close datetime
    print("Matching predictions with source of truth data...")
    
    for idx, pred_row in predictions_df.iterrows():
        pred_title = pred_row['title'].lower().strip()
        pred_time = pred_row['datetime']
        
        # Find potential matches in source data within 24 hours
        time_mask = (source_df['timestamp_created'] >= pred_time - pd.Timedelta(days=1)) & \
                   (source_df['timestamp_created'] <= pred_time + pd.Timedelta(days=1))
        
        potential_matches = source_df[time_mask]
        
        if len(potential_matches) > 0:
            # Simple title matching - check if titles contain similar keywords
            best_match = None
            best_score = 0
            
            for _, source_row in potential_matches.iterrows():
                source_title = source_row['title'].lower().strip()
                
                # Simple word overlap scoring
                pred_words = set(pred_title.split())
                source_words = set(source_title.split())
                
                if len(pred_words) > 0 and len(source_words) > 0:
                    overlap = len(pred_words.intersection(source_words))
                    score = overlap / max(len(pred_words), len(source_words))
                    
                    if score > best_score and score > 0.3:  # 30% overlap threshold
                        best_score = score
                        best_match = source_row
            
            if best_match is not None:
                final_df.at[idx, 'source_of_truth_datetime'] = best_match['timestamp_created']
                final_df.at[idx, 'source_of_truth_sentiment'] = best_match['sentiment']
                final_df.at[idx, 'source_of_truth_confidence'] = best_match['confidence']
                final_df.at[idx, 'is_dow_jones'] = True
    
    # Sort by datetime
    final_df = final_df.sort_values('datetime')
    
    # Save to CSV
    output_file = 'sugar_final_dataset.csv'
    final_df.to_csv(output_file, index=False)
    
    print(f"Final CSV saved to: {output_file}")
    print(f"Total articles: {len(final_df)}")
    print(f"Dow Jones articles matched: {final_df['is_dow_jones'].sum()}")
    print(f"Date range: {final_df['datetime'].min()} to {final_df['datetime'].max()}")
    print(f"Sentiment distribution:")
    print(final_df['sentiment'].value_counts().sort_index())
    print(f"Source of truth sentiment distribution:")
    print(final_df['source_of_truth_sentiment'].value_counts().sort_index())
    
    return final_df

if __name__ == "__main__":
    create_final_sugar_csv()
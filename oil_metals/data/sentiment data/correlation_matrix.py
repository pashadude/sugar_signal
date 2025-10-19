import pandas as pd

# Load oil_only_output.csv, convert all datetimes to UTC, and aggregate by UTC date
from dateutil import parser
import pytz

oil_raw = pd.read_csv('ShinkaEvolve/examples/oil_metals/data/sentiment data/oil_only_output.csv')
if oil_raw.columns[0] != 'datetime':
    oil_raw = pd.read_csv('ShinkaEvolve/examples/oil_metals/data/sentiment data/oil_only_output.csv', names=['datetime', 'sentiment', 'metal', 'Source'])

# Convert to UTC and extract UTC date
def to_utc_date(dt_str):
    dt = parser.isoparse(dt_str)
    dt_utc = dt.astimezone(pytz.UTC)
    return dt_utc.date()

oil_raw['UTC_date'] = oil_raw['datetime'].apply(to_utc_date)

def sentiment_to_num(s):
    if s == 'Positive': return 1
    if s == 'Negative': return -1
    return 0

oil_raw['sentiment_num'] = oil_raw['sentiment'].map(sentiment_to_num)
agg = oil_raw.groupby('UTC_date').agg(
    ZenPulsar_Daily_Oil_Sentiment=('sentiment_num', 'mean'),
    count=('sentiment_num', 'count')
).reset_index()
agg['Date'] = pd.to_datetime(agg['UTC_date'])
oil_df = agg[['Date', 'ZenPulsar_Daily_Oil_Sentiment', 'count']]
oil_df.to_csv('ShinkaEvolve/examples/oil_metals/data/sentiment data/daily_oil_sentiment.csv', index=False)

sentiment_df_raw = pd.read_excel('ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx', sheet_name='Sentiment')
print("sentiment_df_raw columns before rename:", sentiment_df_raw.columns)
print(sentiment_df_raw.head())
sentiment_df = sentiment_df_raw[['Date', 'Daily_Sum_RavenPack']].copy()
sentiment_df['Date'] = pd.to_datetime(sentiment_df['Date'], errors='coerce')
sentiment_df = sentiment_df.dropna(subset=['Date']).reset_index(drop=True)
print("sentiment_df columns after datetime:", sentiment_df.columns)
print("sentiment_df columns repr:", repr(sentiment_df.columns.tolist()))
sentiment_df.columns = sentiment_df.columns.str.strip()
print("sentiment_df columns after strip:", sentiment_df.columns)
print(sentiment_df.head())

ng_df = pd.read_excel('ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx', sheet_name='Natural Gas Future')
ng_df = ng_df[['Date', 'Close']]
ng_df.rename(columns={'Close': 'Natural_Gas_Future_Close'}, inplace=True)
ng_df['Date'] = pd.to_datetime(ng_df['Date'], errors='coerce')
ng_df = ng_df.dropna(subset=['Date']).reset_index(drop=True)
print("ng_df columns after datetime:", ng_df.columns)
print(ng_df.head())

brent_df = pd.read_excel('ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx', sheet_name='Brent')
brent_df = brent_df[['Date', 'Close']]
brent_df.rename(columns={'Close': 'Brent_Close'}, inplace=True)
brent_df['Date'] = pd.to_datetime(brent_df['Date'], errors='coerce')
brent_df = brent_df.dropna(subset=['Date']).reset_index(drop=True)
print("brent_df columns after datetime:", brent_df.columns)
print(brent_df.head())

oil_df = oil_df.reset_index(drop=True)
print("oil_df columns after datetime:", oil_df.columns)
print(oil_df.head())
print("oil_df['Date'] dtype:", oil_df['Date'].dtype)
print("sentiment_df['Date'] dtype:", sentiment_df['Date'].dtype)
print("ng_df['Date'] dtype:", ng_df['Date'].dtype)
print("brent_df['Date'] dtype:", brent_df['Date'].dtype)

# Ensure 'date' is a column, not index, in all DataFrames
oil_df = oil_df.reset_index(drop=True)
sentiment_df = sentiment_df.reset_index(drop=True)
ng_df = ng_df.reset_index(drop=True)
brent_df = brent_df.reset_index(drop=True)

print("oil_df columns before merge:", oil_df.columns)
print("sentiment_df columns before merge:", sentiment_df.columns)
print("ng_df columns before merge:", ng_df.columns)
print("brent_df columns before merge:", brent_df.columns)
print(oil_df.head())
print(sentiment_df.head())
print(ng_df.head())
print(brent_df.head())

# Load Sentiment sheet
sentiment_df = pd.read_excel('ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx', sheet_name='Sentiment')
sentiment_df = sentiment_df[['Date', 'Daily_Sum_RavenPack']]

# Load Natural Gas Future Close
ng_df = pd.read_excel('ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx', sheet_name='Natural Gas Future')
ng_df = ng_df[['Date', 'Close']]
ng_df.rename(columns={'Close': 'Natural_Gas_Future_Close'}, inplace=True)

# Load Brent Close
brent_df = pd.read_excel('ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx', sheet_name='Brent')
brent_df = brent_df[['Date', 'Close']]
brent_df.rename(columns={'Close': 'Brent_Close'}, inplace=True)

# Merge all on date
# Select only needed columns for merge
oil_df_merge = oil_df[['Date', 'ZenPulsar_Daily_Oil_Sentiment']]
sentiment_df_merge = sentiment_df[['Date', 'Daily_Sum_RavenPack']]
print("oil_df_merge columns:", oil_df_merge.columns)
print("sentiment_df_merge columns:", sentiment_df_merge.columns)

df = oil_df_merge.merge(sentiment_df_merge, on='Date', how='inner')
df = df.merge(ng_df, on='Date', how='inner')
df = df.merge(brent_df, on='Date', how='inner')

# Compute correlation matrix
corr = df[['ZenPulsar_Daily_Oil_Sentiment', 'Daily_Sum_RavenPack', 'Natural_Gas_Future_Close', 'Brent_Close']].corr()

import seaborn as sns
import matplotlib.pyplot as plt

print("Correlation matrix:")
print(corr)

# --- Add normalized daily sentiment from ab_25.csv for AC@OIL ---
import numpy as np

ab25 = pd.read_csv('ShinkaEvolve/examples/oil_metals/data/sentiment data/ab_25.csv', sep='\t')
ab25 = ab25[ab25['Commodity'] == 'AC@OIL'].copy()
ab25['Date'] = pd.to_datetime(ab25['Timestamp']).dt.date
ab25_grouped = ab25.groupby('Date').agg(
    ab25_norm_sentiment=('Sentiment', lambda x: np.mean(x))
).reset_index()
ab25_grouped['Date'] = pd.to_datetime(ab25_grouped['Date'])

# Restrict to the date range present in the merged DataFrame
date_min = df['Date'].min()
date_max = df['Date'].max()
ab25_grouped = ab25_grouped[(ab25_grouped['Date'] >= date_min) & (ab25_grouped['Date'] <= date_max)]

# Merge with main DataFrame
df = df.merge(ab25_grouped, on='Date', how='left')

# Rename columns as requested
df = df.rename(columns={
    'Daily_Oil_Sentiment': 'ZenPulsar_Daily_Oil_Sentiment',
    'Daily_Sum_RavenPack': 'RavenPack_Daily_Oil_Sentiment',
    'ab25_norm_sentiment': 'Alexandria_Daily_Oil_Sentiment'
})

# Recompute and plot updated correlation matrix
corr = df[['ZenPulsar_Daily_Oil_Sentiment', 'RavenPack_Daily_Oil_Sentiment', 'Natural_Gas_Future_Close', 'Brent_Close', 'Alexandria_Daily_Oil_Sentiment']].corr()

plt.figure(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
plt.title("Correlation Matrix (with Alexandria, RavenPack, ZenPulsar)")
plt.tight_layout()
plt.savefig("ShinkaEvolve/examples/oil_metals/data/sentiment data/correlation_matrix.png")
print("Updated correlation matrix image saved as correlation_matrix.png")
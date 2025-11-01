"""
Sugar Trading Strategy Evolution
Uses sentiment, price, and options data to generate trading signals
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict

# Data loading utilities
def load_sugar_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load sentiment, price, and options data for sugar

    Returns:
        sentiment_df: DataFrame with datetime index and sentiment/confidence columns
        price_df: DataFrame with datetime index and OHLCV data
        options_df: DataFrame with datetime index and open interest data
    """
    # Use absolute path to data directory (works even when program is copied to results dir)
    import os

    # Strategy: Always use repo root + shinka/examples/sugar for data
    # Shinka sets CWD to repo root when running evaluation
    # This works both when running directly and when copied to results dir
    repo_root = Path(os.getcwd())
    data_dir = repo_root / "shinka" / "examples" / "sugar"

    # Fallback: if data_dir doesn't exist, try to find it relative to this file
    if not data_dir.exists():
        # Get the directory of this script file
        script_dir = Path(__file__).parent.resolve()
        # If we're in results dir, go up to find repo root
        # results/shinka_sugar_trading/DATE/gen_X/ -> need to go up 4 levels
        potential_root = script_dir
        for _ in range(10):  # Try up to 10 parent directories
            test_path = potential_root / "shinka" / "examples" / "sugar"
            if test_path.exists():
                data_dir = test_path
                break
            potential_root = potential_root.parent
            if potential_root == potential_root.parent:  # Reached filesystem root
                break

    # Load sentiment data
    sentiment_df = pd.read_csv(
        data_dir / "sentiment data" / "sugar_final_united_dataset.csv",
        parse_dates=['datetime']
    )
    sentiment_df = sentiment_df.set_index('datetime').sort_index()
    # Remove timezone if present
    if hasattr(sentiment_df.index, 'tz') and sentiment_df.index.tz is not None:
        sentiment_df.index = sentiment_df.index.tz_localize(None)

    # Load price data (strip timezone by converting after loading)
    price_df = pd.read_csv(
        data_dir / "price data" / "SBUSX_5Y_1DAY_FROM_PERPLEXITY.csv"
    )
    # Convert date column to datetime, stripping timezone
    price_df['datetime'] = pd.to_datetime(price_df['date'].str[:10])  # Take only date part, ignore timezone
    price_df = price_df.drop(columns=['date'])
    price_df = price_df.set_index('datetime').sort_index()

    # Load options data (Open Interest)
    options_df = pd.read_csv(
        data_dir / "option data" / "CE Sugar Futures Open Interest (I_ICESFOI).csv"
    )
    options_df['Date'] = pd.to_datetime(options_df['Date'])
    options_df['Value'] = options_df['Value'].str.replace(',', '').astype(float)
    options_df = options_df.rename(columns={'Date': 'datetime', 'Value': 'open_interest'})
    options_df = options_df.set_index('datetime').sort_index()
    # Remove timezone if present
    if hasattr(options_df.index, 'tz') and options_df.index.tz is not None:
        options_df.index = options_df.index.tz_localize(None)

    return sentiment_df, price_df, options_df


def align_data_daily(sentiment_df: pd.DataFrame, price_df: pd.DataFrame,
                     options_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align all data sources to daily frequency
    Sentiment: aggregate daily (mean sentiment, mean confidence)
    Price: already daily
    Options: forward fill weekly data

    Data ranges:
    - Price: 2020-10-26 to 2025-10-24
    - Sentiment: 2021-09-01 to 2025-05-10
    - Options: 2019-08-27 to 2025-09-23

    Common period: 2021-09-01 to 2025-05-10
    """
    # Aggregate sentiment to daily
    sentiment_daily = sentiment_df.resample('D').agg({
        'sentiment': 'mean',
        'confidence': 'mean'
    })
    # Ensure tz-naive
    if hasattr(sentiment_daily.index, 'tz') and sentiment_daily.index.tz is not None:
        sentiment_daily.index = sentiment_daily.index.tz_localize(None)

    # Create weighted sentiment (sentiment * confidence)
    sentiment_daily['weighted_sentiment'] = (
        sentiment_daily['sentiment'] * sentiment_daily['confidence']
    )

    # Resample options to daily (forward fill)
    options_daily = options_df.resample('D').ffill()
    # Ensure tz-naive
    if hasattr(options_daily.index, 'tz') and options_daily.index.tz is not None:
        options_daily.index = options_daily.index.tz_localize(None)

    # Merge all data on daily frequency
    df = price_df.copy()
    df = df.join(sentiment_daily, how='left')
    df = df.join(options_daily, how='left')

    # Forward fill missing sentiment and options data
    df = df.ffill().bfill()

    # Final check - ensure result is tz-naive
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # Filter to common date range (limited by sentiment data)
    # Sentiment starts: 2021-09-01, ends: 2025-05-10
    start_date = pd.to_datetime('2021-09-01')
    end_date = pd.to_datetime('2025-05-10')
    df = df[(df.index >= start_date) & (df.index <= end_date)]

    return df


# EVOLVE-BLOCK-START
def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def generate_trading_signals(df: pd.DataFrame) -> pd.Series:
    """
    Generate trading signals based on 17 alpha strategies

    Returns:
        signals: pd.Series with values -1 (short), 0 (neutral), 1 (long)
    """
    signals = pd.Series(0, index=df.index, dtype=float)

    # Extract key series
    price = df['close']
    sentiment = df['sentiment']
    weighted_sentiment = df['weighted_sentiment']
    volume = df['volume']
    open_interest = df['open_interest']

    # Calculate additional indicators
    volatility = price.pct_change().rolling(window=20).std()
    rsi = calculate_rsi(price, window=14)

    # ===== 17 ALPHA STRATEGIES =====

    # 1. alpha_price_sent_reaction - Price drift after sentiment events
    sentiment_change = sentiment.diff()
    sentiment_std = sentiment_change.rolling(window=252).std()
    sentiment_events = sentiment_change.abs() > sentiment_std
    alpha_1 = sentiment_events.astype(float) * np.sign(sentiment_change)

    # 2. alpha_sentiment_price_corr - Rolling correlation
    rolling_corr = sentiment.rolling(window=30).corr(price)
    # Replace inf/NaN with 0 (happens when series has zero variance in window)
    alpha_2 = rolling_corr.replace([np.inf, -np.inf], 0).fillna(0)

    # 3. alpha_sentiment_price_divergence - Contrarian when diverging
    price_change = price.pct_change()
    divergence = (np.sign(price_change) != np.sign(sentiment_change))
    alpha_3 = -1 * divergence.astype(float)

    # 4. alpha_sentiment_price_inversion - Trade on correlation flips
    regime_flip = (rolling_corr.shift(1) * rolling_corr) < 0
    alpha_4 = np.where(regime_flip, -np.sign(rolling_corr.shift(1)), np.sign(rolling_corr))
    alpha_4 = pd.Series(alpha_4, index=df.index).fillna(0)

    # 5. alpha_weighted_sent_leading_price - Weighted sentiment as leading indicator
    alpha_5 = weighted_sentiment.shift(1).fillna(0)
    alpha_5 = (alpha_5 - alpha_5.mean()) / (alpha_5.std() + 1e-8)

    # 6. alpha_weighted_sent_price_corr - Rolling correlation with weighted sentiment
    alpha_6 = weighted_sentiment.rolling(window=30).corr(price).replace([np.inf, -np.inf], 0).fillna(0)

    # 7. alpha_sent_vol_corr - Sentiment-volume correlation (conviction gauge)
    alpha_7 = sentiment.rolling(window=30).corr(volume).replace([np.inf, -np.inf], 0).fillna(0)

    # 8. alpha_sentiment_volatility_corr - Bullish sentiment + low vol
    bullish = sentiment > sentiment.quantile(0.7)
    low_vol = volatility < volatility.quantile(0.3)
    alpha_8 = (bullish & low_vol).astype(float) - (~bullish & ~low_vol).astype(float)

    # 9. alpha_dollar_cov_sent_rsi - Multi-factor model (price momentum + sentiment + RSI)
    price_momentum = price.pct_change(periods=5)
    alpha_9 = (price_momentum * sentiment * (rsi / 100)).fillna(0)
    alpha_9 = (alpha_9 - alpha_9.mean()) / (alpha_9.std() + 1e-8)

    # 10. alpha_volume_sentiment_correlation
    alpha_10 = volume.rolling(window=30).corr(sentiment).replace([np.inf, -np.inf], 0).fillna(0)

    # 11. alpha_weighted_sent_volume_corr
    alpha_11 = volume.rolling(window=30).corr(weighted_sentiment).replace([np.inf, -np.inf], 0).fillna(0)

    # 12. alpha_weighted_sent_rsi_price_corr - Combined confirmation
    trend = price.pct_change().apply(np.sign)
    alpha_12 = (weighted_sentiment * (rsi / 100) * trend).fillna(0)
    alpha_12 = (alpha_12 - alpha_12.mean()) / (alpha_12.std() + 1e-8)

    # 13. alpha_cs_sent_breadth_supply - Sentiment breadth / supply factor
    sentiment_strength = sentiment.rolling(window=20).mean()
    supply_proxy = volume.rolling(window=20).mean()
    alpha_13 = (sentiment_strength / (supply_proxy / supply_proxy.mean() + 0.1)).fillna(0)
    alpha_13 = (alpha_13 - alpha_13.mean()) / (alpha_13.std() + 1e-8)

    # 14. alpha_pit_cov_breadth - Rolling covariance of sentiment and volatility
    alpha_14 = sentiment.rolling(window=30).cov(volatility).replace([np.inf, -np.inf], 0).fillna(0)
    alpha_14 = (alpha_14 - alpha_14.mean()) / (alpha_14.std() + 1e-8)

    # 15. alpha_8_sent_oi_divergence_cov - Sentiment vs Open Interest divergence
    sent_trend = sentiment.diff().rolling(5).mean()
    oi_trend = open_interest.diff().rolling(5).mean()
    oi_divergence = (np.sign(sent_trend) != np.sign(oi_trend))
    alpha_15 = -1 * oi_divergence.astype(float)

    # 16. alpha_sentiment_import_fee_cov - Sentiment / volatility (stability factor)
    alpha_16 = (sentiment * (1 / (volatility + 0.001))).fillna(0)
    alpha_16 = (alpha_16 - alpha_16.mean()) / (alpha_16.std() + 1e-8)

    # 17. alpha_sentiment_proc_fee - Sentiment with exponential volatility decay
    alpha_17 = (sentiment * np.exp(-volatility * 10)).fillna(0)
    alpha_17 = (alpha_17 - alpha_17.mean()) / (alpha_17.std() + 1e-8)

    # ===== COMBINE ALPHAS WITH EVOLVABLE WEIGHTS =====
    # These weights will be optimized by Shinka evolution
    w1 = 1.0
    w2 = 1.0
    w3 = 0.5
    w4 = 0.5
    w5 = 1.5
    w6 = 1.0
    w7 = 0.8
    w8 = 1.2
    w9 = 1.0
    w10 = 0.8
    w11 = 0.8
    w12 = 1.2
    w13 = 0.5
    w14 = 0.5
    w15 = 1.0
    w16 = 0.8
    w17 = 0.8

    combined_alpha = (
        w1 * alpha_1 +
        w2 * alpha_2 +
        w3 * alpha_3 +
        w4 * alpha_4 +
        w5 * alpha_5 +
        w6 * alpha_6 +
        w7 * alpha_7 +
        w8 * alpha_8 +
        w9 * alpha_9 +
        w10 * alpha_10 +
        w11 * alpha_11 +
        w12 * alpha_12 +
        w13 * alpha_13 +
        w14 * alpha_14 +
        w15 * alpha_15 +
        w16 * alpha_16 +
        w17 * alpha_17
    )

    # Normalize combined alpha
    combined_alpha = (combined_alpha - combined_alpha.mean()) / (combined_alpha.std() + 1e-8)

    # Generate signals with evolvable thresholds
    # Initial thresholds are more permissive to ensure some trading activity
    # For z-score normalized signal (mean=0, std=1):
    # - threshold ±0.3 captures ~38% of distribution tails
    # - threshold ±0.5 captures ~30% of distribution tails
    # Start with ±0.3 to ensure initial trades, evolution will optimize
    long_threshold = 0.3
    short_threshold = -0.3

    signals[combined_alpha > long_threshold] = 1.0
    signals[combined_alpha < short_threshold] = -1.0

    return signals


def backtest_strategy(df: pd.DataFrame, signals: pd.Series,
                     cost_per_side: float = 2.97,
                     capital: float = 50000.0) -> Dict:
    """
    Backtest the trading strategy with realistic IB Sugar #11 futures costs

    Args:
        df: DataFrame with price data
        signals: Trading signals (-1, 0, 1)
        cost_per_side: Total cost per contract per side ($2.97 default)
        capital: Starting capital in USD ($50,000)

    Returns:
        Dictionary with performance metrics

    Cost Breakdown (per contract, per side):
        - Broker Commission (IBKR):    $0.85
        - Exchange Fee (ICE US):       $2.10
        - Regulatory Fee (CFTC):       $0.02
        - Clearing Fee:                $0.00 (included in exchange fee)
        ─────────────────────────────────────
        Total per side:                $2.97
        Total round-trip (open+close): $5.94

    Position changes in this strategy represent ROUND TRIPS (entry + exit),
    so we use the full round-trip cost of $5.94 per position change.

    As percentage of $50k capital: $5.94 / $50,000 = 0.01188% per round-trip
    """
    # Calculate returns
    returns = df['close'].pct_change()

    # Calculate position changes (for commission calculation)
    # Each position_change represents a round trip (exit old + enter new)
    position_changes = signals.diff().abs()

    # Strategy returns = signal * future return
    strategy_returns = signals.shift(1) * returns

    # Calculate round-trip cost as percentage of capital
    # Round-trip = 2 * cost_per_side = $5.94
    round_trip_cost = 2 * cost_per_side
    commission_pct = round_trip_cost / capital

    # Subtract commissions on position changes
    strategy_returns = strategy_returns - (position_changes * commission_pct)

    # Calculate cumulative returns
    cum_returns = (1 + strategy_returns).cumprod()

    # Calculate metrics
    total_return = cum_returns.iloc[-1] - 1 if len(cum_returns) > 0 else 0

    # Sharpe ratio (annualized, assuming 252 trading days)
    sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / (strategy_returns.std() + 1e-8)

    # Maximum drawdown
    rolling_max = cum_returns.expanding().max()
    drawdowns = (cum_returns - rolling_max) / rolling_max
    max_drawdown = drawdowns.min()

    # Number of trades
    num_trades = position_changes.sum()

    # Win rate
    winning_trades = (strategy_returns > 0).sum()
    total_trades = (strategy_returns != 0).sum()
    win_rate = winning_trades / (total_trades + 1e-8)

    metrics = {
        'total_return': float(total_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'num_trades': float(num_trades),
        'win_rate': float(win_rate),
        'mean_return': float(strategy_returns.mean()),
        'std_return': float(strategy_returns.std())
    }

    return metrics

# EVOLVE-BLOCK-END


def run_experiment(**kwargs) -> Dict:
    """
    Main experiment function called by evaluator

    Returns:
        Dictionary with performance metrics
    """
    # Load and align data
    sentiment_df, price_df, options_df = load_sugar_data()
    df = align_data_daily(sentiment_df, price_df, options_df)

    # Drop NaN values
    df = df.dropna()

    # IMPORTANT: Generate signals on FULL dataset first
    # This ensures rolling windows have enough history
    # Then we split and evaluate only on validation set
    signals = generate_trading_signals(df)

    # Split into train/validation if specified
    val_ratio = kwargs.get('val_ratio', 0.3)
    split_idx = int(len(df) * (1 - val_ratio))

    # Use validation set for evaluation (but with signals from full data)
    val_df = df.iloc[split_idx:]
    val_signals = signals.iloc[split_idx:]

    # Backtest strategy on validation set only
    # Using realistic IB fees: $2.97/side × 2 = $5.94 round-trip with $50k capital
    metrics = backtest_strategy(val_df, val_signals,
                                cost_per_side=2.97,
                                capital=50000.0)

    return metrics

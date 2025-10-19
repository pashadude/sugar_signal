config = AlphaConfig(start_date = '2010-01-01', neutralization = 'market')
def alpha_lme_on_warrant_extreme(s: Streams, window=252, lower_threshold=-3, upper_threshold=3) -> pd.DataFrame:
    """
    Thesis: A significant decline in LME warrant stock levels over a 3-month period indicates a sustained tightening 
    of refined market fundamentals, reflecting a structural supply-demand imbalance. 

    This trend suggests that refined metal availability has decreased substantially, which often leads to upward price movement. 
    By focusing on a 3-month timeframe, we avoid short-term noise and gain confidence that the observed tightening is 
    fundamental rather than transient.

    The function generates binary trading signals:
      - 1: Buy signal (z < lower_threshold) when stocks show extreme depletion.
      - -1: Sell signal (z > upper_threshold) when stocks show extreme build-up.
      - 0: Neutral (no extreme conditions met).
    """
    # Step 1: Apply a 1-period lag to the LME warrant stock data to avoid lookahead bias
    lme_on_warrant_delayed = ts_delay(s.lme_on_warrant, 1)
    
    # Step 2: Calculate 3-month percent changes (63 trading days)
    # Using 21 trading days as a month, 3 months = 21 * 3
    pct_change = lme_on_warrant_delayed.pct_change(21 * 3)
    
    # Step 3: Compute z-scores over the rolling window
    # z-score = (value - rolling mean) / rolling standard deviation
    rolling_mean = ts_mean(pct_change, window)
    rolling_std = ts_stddev(pct_change, window)
    z_scores = (pct_change - rolling_mean) / rolling_std
    
    # Step 4: Generate binary trading signals based on z-score thresholds
    signals = z_scores.copy()
    signals[z_scores < lower_threshold] = 1  # Buy signal: z < lower_threshold (extreme depletion)
    signals[z_scores > upper_threshold] = -1  # Sell signal: z > upper_threshold (extreme build-up)
    signals[(z_scores >= lower_threshold) & (z_scores <= upper_threshold)] = 0  # Neutral signal

    return signals
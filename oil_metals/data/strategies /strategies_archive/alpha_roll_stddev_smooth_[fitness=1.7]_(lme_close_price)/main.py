config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_roll_stddev_smooth(s: Streams, lookback=7, smooth_window=11):
    """
    Standardize the Price relative to its rolling mean and std,
    then smooth.  A typical mean-reversion approach.
    Hypothesis:
      - If price is far above its mean (positive z-score), expect reversion => short.
      - If below its mean (negative z-score), expect reversion => long.
    """
    mean_val = ts_mean(s.lme_close_price, window=lookback)
    std_val = ts_stddev(s.lme_close_price, window=lookback)
    zscore_raw = safe_div(s.lme_close_price - mean_val, std_val)
    # Additional smoothing
    zscore_smooth = ts_mean(zscore_raw, window=smooth_window)
    return -zscore_smooth
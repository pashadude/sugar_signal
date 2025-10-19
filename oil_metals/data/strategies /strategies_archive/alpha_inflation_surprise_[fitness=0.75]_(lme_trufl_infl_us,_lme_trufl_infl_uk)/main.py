config = AlphaConfig(booksize = 10000000.0, start_date = '2020-01-01', end_date = '2024-12-01')
def alpha_inflation_surprise(s: Streams, surprise_window=5, smooth_window=5, use_uk=True):
    """
    Compare today's inflation reading to a short moving average, 
    treating large deviations as 'surprise' days.
    Hypothesis:
      - If today's inflation is well above the recent average => bullish or short 
        depending on how metals historically react to inflation shocks.
    """
    infl_series = s.lme_trufl_infl_uk if use_uk else s.lme_trufl_infl_us
    
    # 1) Short moving average
    infl_ma = ts_mean(infl_series, window=surprise_window)
    
    # 2) Surprise factor
    surprise_raw = infl_series - infl_ma
    
    # 3) Optionally smooth
    surprise_smooth = ts_mean(surprise_raw, window=smooth_window)
    
    return surprise_smooth
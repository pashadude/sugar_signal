config = AlphaConfig(booksize = 10000000.0, start_date = '2019-12-06', end_date = '2024-12-05', neutralization = 'market')
def alpha_inflation_roc_contrarian_uk(s: Streams, window=10, smooth_window=10, use_uk=True):
    """
    Rate-of-change (ROC) of inflation vs. short-term price returns. 
    Contrarian logic: if inflation ROC is high but price return hasn't followed, 
    or vice versa, bet on reversion.
    """
    if use_uk:
        infl_series = s.lme_trufl_infl_uk
    else:
        infl_series = s.lme_trufl_infl_us

    # 1) Rate-of-change of inflation over 'window' days
    infl_roc = ts_pct_change(infl_series, periods=window)
    
    # 2) Rate-of-change of price
    price_roc = ts_pct_change(s.lme_close_price, periods=window)
    
    # 3) Difference between the two
    roc_diff = infl_roc - price_roc
    
    # 4) Smooth
    diff_smooth = ts_mean(roc_diff, window=smooth_window)
    
    return diff_smooth
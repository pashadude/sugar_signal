config = AlphaConfig()
def alpha_corr_gas_oil(s: Streams, corr_window=12, smooth_window=5):
    """
    Rolling correlation between the LME close price and Gas Oil (diesel),
    smoothed to reduce turnover.

    Hypothesis:
      - If correlation is high, metals and diesel costs are moving similarly, 
        indicating industrial demand or cost-driven price changes.
      - Low/negative correlation suggests other metal-specific factors 
        dominating over diesel cost influences.
    """
    corr_raw = s.lme_close_price.rolling(corr_window).corr(s.lme_gas_oil1)
    corr_smooth = ts_mean(corr_raw, window=smooth_window)
    return corr_smooth
config = AlphaConfig()
def alpha_corr_brent(s: Streams, corr_window=30, smooth_window=2):
    """
    Rolling correlation between the LME close price and Brent oil,
    then smoothed to reduce noise.

    Hypothesis:
      - High positive correlation suggests metals and oil are moving together,
        possibly reflecting a broad commodity cycle or inflationary environment.
      - Low/negative correlation may indicate metal-specific supply/demand factors 
        dominating energy costs.
    """
    corr_raw = s.lme_close_price.rolling(corr_window).corr(s.lme_brent_oil)
    corr_smooth = ts_mean(corr_raw, window=smooth_window)
    return corr_smooth
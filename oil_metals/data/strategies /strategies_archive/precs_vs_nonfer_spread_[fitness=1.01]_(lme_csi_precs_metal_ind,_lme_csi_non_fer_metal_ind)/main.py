config = AlphaConfig(booksize = 10000000.0)
def precs_vs_nonfer_spread(s: Streams, window=10, smooth_window=5):
    """
    Compare Precious Metals Index vs. Non-Ferrous Metal Index,
    then measure difference in their short-term trends.

    Hypothesis:
      - If precious metals are outperforming non-ferrous metals,
        it might be risk-off or safe-haven rotation => bullish for certain LME metals
        if they follow precious behavior or negative if they diverge.
      - If non-ferrous is outperforming, it could reflect stronger industrial demand => bullish for base metals.
    """
    # Short-term changes in precious metals index
    precs_ret = ts_pct_change(s.lme_csi_precs_metal_ind, periods=window)
    # Short-term changes in non-ferrous metals index
    nonfer_ret = ts_pct_change(s.lme_csi_non_fer_metal_ind, periods=window)
    
    # Spread
    spread = precs_ret - nonfer_ret
    # smooth
    spread = ts_mean(spread, window=smooth_window)

    return -spread
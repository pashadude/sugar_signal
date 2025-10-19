config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_coal_metals(s: Streams, window=20, smooth_window=5):
    """
    Compare short-term returns of CSI Coal Index to LME metal.
    Hypothesis (Energy/Production Cost):
      - Coal is used in smelting, especially for certain metals (steel/copper smelting).
      - If coal prices rise without a similar metal price move, producers might reduce output => bullish.
    """
    coal_ret = ts_pct_change(s.lme_csi_coal_ind, periods=window)
    metal_ret = ts_pct_change(s.lme_close_price, periods=window)
    
    divergence = coal_ret - metal_ret
    return -ts_mean(divergence, window=smooth_window)
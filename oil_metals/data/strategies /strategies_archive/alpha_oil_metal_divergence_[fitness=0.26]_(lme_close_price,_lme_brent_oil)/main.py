config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_oil_metal_divergence(s: Streams, window=20, smooth_window=5):
    """
    Compare short-term returns of Brent oil and the metal's price.
    Hypothesis (Energy Cost):
      - High oil prices raise production and transportation costs for metals, 
        potentially limiting supply (bullish) or compressing margins (bearish depending on pass-through).
      - Divergence between oil and metals might indicate cost-pressure vs. demand mismatch.
    """
    # Short-term returns
    oil_ret = ts_pct_change(s.lme_brent_oil, periods=window)
    metal_ret = ts_pct_change(s.lme_close_price, periods=window)
    
    divergence = oil_ret - metal_ret
    
    # Optional smoothing to reduce turnover
    return ts_mean(divergence, window=smooth_window)
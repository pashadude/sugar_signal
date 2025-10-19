config = AlphaConfig(booksize = 10000000.0)
def alpha_env_corr(s: Streams, corr_window=20, smooth_window=5):
    """
    Rolling correlation between metal price and CSI Environmental Protection Index.
    
    Hypothesis:
      - Environmental policies or 'green' sentiment can constrain supply 
        (stricter emissions, etc.) or shift demand to certain metals.
      - High correlation => metals moving with env sector, 
        possibly a macro/regulatory theme.
    """
    corr_raw = s.lme_close_price.rolling(corr_window).corr(s.lme_csi_env_protect_ind)
    corr_smooth = ts_mean(corr_raw, window=smooth_window)
    
    return corr_smooth
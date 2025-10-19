config = AlphaConfig(booksize = 10000000.0)
def alpha_env_coal_ratio(s: Streams, window=10, smooth_window=5):
    """
    Compute the ratio of CSI Environmental Protection Index to CSI Coal Index,
    then compare short-term returns or level to see policy/regulatory influences.

    Hypothesis:
      - If 'env_protect' outpaces 'coal', environmental constraints or green initiatives 
        could limit fossil usage => potential supply constraints for certain metals => bullish.
      - If coal outperforms, traditional energy might remain strong => different effect on metals.
    """
    coal_vals = s.lme_csi_coal_ind
    env_vals  = s.lme_csi_env_protect_ind

    # Ratio
    ratio_raw = safe_div(env_vals, coal_vals)
    
    # Rolling short-term returns on this ratio
    ratio_ret = ts_pct_change(ratio_raw, periods=window)
    ratio_smooth = ts_mean(ratio_ret, window=smooth_window)
    return ratio_smooth
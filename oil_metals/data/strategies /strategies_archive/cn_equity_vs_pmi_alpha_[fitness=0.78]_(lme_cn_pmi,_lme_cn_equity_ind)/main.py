config = AlphaConfig()
def cn_equity_vs_pmi_alpha(s: Streams, window=5) -> pd.DataFrame:
    """
    Hypothesis:
    Investor flows between equities and commodities shift across economic stages:
      1. Economy strong, equities bid: Commodities underperform as funds rotate into equities.
      2. Economy strong, equities weaken: Commodities gain as investors rotate out of equities.
      3. Economy weak, equities weak: Both equities and commodities sell off.
      4. Economy weak, equities rebound: Commodities follow equities, anticipating recovery.
 
    """
    # Lag the PMI to avoid lookahead bias.
    # We apply a 30-day lag to the PMI data to ensure that we are not using future information
    # when evaluating the relationship with equity performance.
    delayed_pmi = ts_delay(s.lme_cn_pmi.ffill(), 30)
    
    # Get China SSE index
    cn_equity = s.lme_cn_equity_ind

    # Compute rolling negative correlation between lagged PMI and equities.
    res = -correlation(delayed_pmi, cn_equity, window)

    # Return the resulting alpha signal, representing rolling correlations aligned with the hypothesis.
    return res
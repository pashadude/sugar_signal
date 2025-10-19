config = AlphaConfig()
def alpha_fed_rate_mean_reversion(s:Streams):
    """
    Hypothesis: Positive deviation from the average Federal Funds Rate reduces liquidity in financial markets,
    potentially lowering base metal prices due to increased borrowing costs.
    """
    fed_rate = ts_ffill(s.lme_us_fed_rate)
    fed_rate_mean_reversion = fed_rate - ts_mean(fed_rate, window=month_2)
    return - fed_rate_mean_reversion
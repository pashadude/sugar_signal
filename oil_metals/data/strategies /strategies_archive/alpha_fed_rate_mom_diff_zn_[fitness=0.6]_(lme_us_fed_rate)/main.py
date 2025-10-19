config = AlphaConfig()
def alpha_fed_rate_mom_diff_zn(s:Streams):
    """
    Hypothesis: The normalized gap between short-term and medium-term Federal Funds Rate trends reflects shifts in monetary policy.
    A decreasing trend suggests easing, potentially increasing base metal demand and prices,
    while an increasing trend indicates tightening, likely reducing demand and prices.
    """
    fed_rate = delta(ts_ffill(s.lme_us_fed_rate), period=month)
    fed_rate_2mma = ts_mean(fed_rate, window=month_2)
    fed_rate_3mma = ts_mean(fed_rate, window=quarterly)
    fed_rate_diff = fed_rate_2mma - fed_rate_3mma
    fed_rate_diff_zn = zscore(fed_rate_diff, window=quarterly)
    return - ts_mean(fed_rate_diff_zn, window=quarterly)
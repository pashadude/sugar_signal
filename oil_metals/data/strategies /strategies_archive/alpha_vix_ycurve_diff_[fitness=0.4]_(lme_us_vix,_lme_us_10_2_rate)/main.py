config = AlphaConfig()
def alpha_vix_ycurve_diff(s: Streams):
    """
    Hypothesis: Increasing short-term market volatility combined with rising inflation may lead to an inflation shock,
    causing a short-term boost in commodity prices. However, in the medium term, prices are likely to decrease
    as the effects of the shock subside.
    """
    vix_perc = ts_pct_change(s.lme_us_vix, periods=week)
    us_10_2_rate_perc = ts_pct_change(s.lme_us_10_2_rate, periods=week)
    vix_perc_ma10 = ts_mean(vix_perc, window=week_2)
    us_10_2_rate_perc_ma10 = ts_mean(us_10_2_rate_perc, window=week_2)
    vix_perc_ma20 = ts_mean(vix_perc_ma10, window=week_2)
    us_10_2_rate_perc_ma20 = ts_mean(us_10_2_rate_perc_ma10, window=week_2)
    vix_yield_momentum = (vix_perc_ma10 - vix_perc_ma20) - (us_10_2_rate_perc_ma10 - us_10_2_rate_perc_ma20)
    return - vix_yield_momentum
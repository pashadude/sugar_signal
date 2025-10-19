config = AlphaConfig()
def alpha_ycurve_dep_cor(s: Streams):
    """
    Hypothesis: The negative correlation between U.S. deposit growth and the 10-2 Treasury spread suggests
    that rising deposits with a flattening yield curve may indicate risk aversion, potentially lowering base metal prices.
    """
    us_10_2_rate = delta(s.lme_us_10_2_rate, period=week)
    dep_instit = delta(ts_ffill(s.lme_us_dep_instit), period=week)
    us_10_2_rate_ma15 = ts_mean(us_10_2_rate, window=week_2)
    dep_instit_ma15 = ts_mean(dep_instit, window=week_2)
    return correlation(dep_instit_ma15, us_10_2_rate_ma15, window=week)
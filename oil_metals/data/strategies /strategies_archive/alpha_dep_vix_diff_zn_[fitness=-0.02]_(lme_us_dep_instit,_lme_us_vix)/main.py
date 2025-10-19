config = AlphaConfig()
def alpha_dep_vix_diff_zn(s: Streams):
    """
    Hypothesis: Positive percentage difference between deposits from banks and non-banking institutions,
    relative to market volatility, suggests potential market stability and consistent demand for commodities,
    including base metals, leading to a rise in their prices. Conversely, the opposite effect may occur
    in the case of increased volatility.
    """
    dep_instit_perc = ts_pct_change(ts_ffill(s.lme_us_dep_instit), periods=week_2)
    vix_perc = ts_pct_change(s.lme_us_vix, periods=week_2)
    dep_vix_diff = dep_instit_perc - vix_perc
    return zscore(dep_vix_diff, window=week_2)
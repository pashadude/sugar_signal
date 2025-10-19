config = AlphaConfig()
def unemp_treas_ratio(s:Streams):
    """
    Hypothesis: The ratio of Unemployment Rate changes to Treasury Balance changes reflects economic stress.
    A higher ratio (negative signal) suggests worsening labor market conditions relative to government liquidity,
    potentially signaling weaker base metal demand.
    """
    unemp_diff = delta(ts_ffill(s.lme_us_unemp_rate), period=month_2)
    tres_bal_diff = delta(ts_ffill(s.lme_us_tres_bal), period=week_2)
    unemp_diff_wma = zscore(ts_delay(ts_mean(unemp_diff, window=week_2), period=week_2), window=week_3)
    tres_bal_diff_wma = zscore(ts_mean(tres_bal_diff, window=week_2), window=week_2)
    unemp_treas_ratio = safe_div(unemp_diff_wma, tres_bal_diff_wma)
    return - unemp_treas_ratio
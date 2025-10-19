config = AlphaConfig()
def construction_vix_ratio_diff(s:Streams):
    """
    Hypothesis: The VIX-to-Construction Spending Ratio compares market volatility to construction activity growth.
    Rising volatility relative to construction slowdowns may signal weaker economic conditions and lower base metal demand.
    """
    vix_diff = delta(s.lme_us_vix, period=week_2)
    construct_spend_diff = ts_delay(delta(ts_ffill(s.lme_us_constr_spend), period=month), period=month_2)
    construct_spend_diff_wma2 = ts_ewm(construct_spend_diff, span=month, adjust=True, min_periods=1, ignore_na=False)
    vix_diff_wma2 = ts_ewm(vix_diff, span=month, adjust=True, min_periods=1, ignore_na=False)
    vix_construct_spend_ratio_zn = zscore(safe_div(vix_diff_wma2, construct_spend_diff_wma2), window=month_4)
    return -delta(vix_construct_spend_ratio_zn, period=quarterly)
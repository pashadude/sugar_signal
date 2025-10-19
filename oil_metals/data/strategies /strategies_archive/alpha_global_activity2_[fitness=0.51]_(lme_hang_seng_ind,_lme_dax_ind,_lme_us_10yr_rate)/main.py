config = AlphaConfig(booksize = 10000000.0)
def alpha_global_activity2(s: Streams, window=15, roc_periods=5):
    """
    Combines signals from the Hang Seng, DAX, and US 10-Year Rate to create a proxy for global economic activity.
    - Long when Hang Seng and DAX are rising, and US 10-Year Rates are falling (risk-on environment).
    - Short when Hang Seng and DAX are falling, and US 10-Year Rates are rising (risk-off environment).
    """
    hang_seng_roc = ts_pct_change(s.lme_hang_seng_ind, periods=roc_periods)
    dax_roc = ts_pct_change(s.lme_dax_ind, periods=roc_periods)
    inverted_us10yr_delta = -delta(s.lme_us_10yr_rate, period=roc_periods)

    combined_signal = scale(hang_seng_roc) + scale(dax_roc) + scale(inverted_us10yr_delta)

    return zscore(combined_signal, window=window)
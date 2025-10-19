config = AlphaConfig()
def us_trade_bal_cn_gdp_corr(s:Streams):
    """
    The US Trade Balance-China GDP Correlation reflects economic ties between the two nations.
    A positive signal suggests stronger trade-GDP alignment, supporting base metal prices,
    while a negative signal indicates weaker economic ties, potentially leading to price declines.
    As China's GDP growth weakens its link to the US trade balance, the signal’s direction may shift,
    impacting base metal prices.
    """
    us_trade_bal_cn_gdp_corr = correlation(
        zscore(ts_ffill(s.lme_us_trade_bal), window=month_4),
        zscore(ts_ffill(s.lme_cn_gdp), window=month_7),
        window=month_9)
    return us_trade_bal_cn_gdp_corr
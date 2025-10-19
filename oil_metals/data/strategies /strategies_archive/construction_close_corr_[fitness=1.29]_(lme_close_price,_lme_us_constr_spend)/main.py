config = AlphaConfig()
def construction_close_corr(s:Streams):
    """
    Hypothesis: The Construction-Close Price Correlation measures the relationship between U.S. construction spending growth and base metal price changes.
    A positive correlation suggests stronger construction activity aligns with rising base metal prices,
    while a negative correlation indicates weaker demand pressure on prices.
    """
    construction_3mma = ts_delay(ts_mean(ts_pct_change(ts_ffill(s.lme_us_constr_spend), periods=month), window=quarterly), period=month)
    close_price_3mma = ts_mean(ts_pct_change(s.lme_close_price, periods=week), window=quarterly)
    construction_close_corr = correlation(construction_3mma, close_price_3mma, window=month)
    return construction_close_corr
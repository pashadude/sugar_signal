config = AlphaConfig()
def alpha_fed_rate_close_price_corr(s:Streams):
    """
    # Hypothesis: Price of base metals increases in the same direction as the Federal Funds Rate (rate at which banks lend money to the market).
    """
    fed_rate = ts_pct_change(ts_ffill(s.lme_us_fed_rate), periods=month)
    close_price = ts_pct_change(s.lme_close_price, periods=month)
    fed_rate_3mma = ts_mean(fed_rate, window=quarterly)
    close_price_3mma = ts_mean(close_price, window=quarterly)
    fed_rate_close_corr = correlation(fed_rate_3mma, close_price_3mma)
    return fed_rate_close_corr
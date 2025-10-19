config = AlphaConfig(neutralization = 'market')
def alpha_price_to_stock_corr(
        s: Streams,
        window=4
) -> pd.DataFrame:
    """
    Hypothesis: high moving correlation between price and its stock
    will retain its value ahead
    """

    res = correlation(s.lme_close_price, s.lme_closing_stock, window)
    res = ts_ewm(res, span=window, min_periods=window)
    res = rank(res)

    return res
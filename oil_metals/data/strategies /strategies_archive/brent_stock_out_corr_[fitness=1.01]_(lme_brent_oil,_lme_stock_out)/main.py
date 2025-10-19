config = AlphaConfig()
def brent_stock_out_corr(
        s: Streams,
        window=20,
        delay_window=0
) -> pd.DataFrame:
    """
    Hypothesis: correlation between brent oil and stock outflow could indicate the demand
    for the metals in stocks.
    """
    brent = ts_delay(s.lme_brent_oil, delay_window)

    return correlation(brent, s.lme_stock_out, window)
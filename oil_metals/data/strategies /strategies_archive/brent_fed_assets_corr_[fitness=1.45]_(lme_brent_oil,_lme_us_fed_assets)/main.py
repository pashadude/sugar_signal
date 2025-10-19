config = AlphaConfig()
def brent_fed_assets_corr(
        s: Streams,
        window=30,
        delay_window=0
) -> pd.DataFrame:
    """
    Hypothesis: a strong positive correlation would suggest that monetary expansion
    tends to support oil prices, while tightening could suppress them. Oil prices
    could be indicator to the commodity metals demand
    """
    brent = ts_delay(s.lme_brent_oil, delay_window)
    fed = ts_mean(ts_ffill(s.lme_us_fed_assets), window)

    return correlation(brent, fed, window)
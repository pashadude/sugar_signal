config = AlphaConfig()
def brent_on_warrant_corr(
        s: Streams,
        window=20,
        delay_window=0
) -> pd.DataFrame:
    """
    Hypothesis: rising oil prices might push investors to turn to commodities,
    therefore reducing the size on_warrant and making a demand increase
    """
    brent = ts_delay(s.lme_brent_oil, delay_window)

    return -correlation(brent, s.lme_on_warrant, window)
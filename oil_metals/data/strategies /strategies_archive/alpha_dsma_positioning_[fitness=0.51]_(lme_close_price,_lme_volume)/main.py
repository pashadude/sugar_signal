config = AlphaConfig()
def alpha_dsma_positioning(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    Fake Trend Reversal within Bigger Trend

    - Short: Closing Price > 3-day SMA AND Closing Price < 10-day SMA.
    - Long: Closing Price < 3-day SMA AND Closing Price > 10-day SMA.
    """

    res = ((((s.lme_close_price >= ts_mean(s.lme_close_price, window=3)) &
           (s.lme_close_price <= ts_mean(s.lme_close_price, window=10)) * -1)
           + ((s.lme_close_price <= ts_mean(s.lme_close_price, window=3)) &
              (s.lme_close_price >= ts_mean(s.lme_close_price, window=10)) * 1))) * s.lme_volume

    return res
config = AlphaConfig(start_date = '2016-01-01', neutralization = 'market')
def alpha_us_cpi(
        s: Streams,
) -> pd.DataFrame:
    """
    Hypothesis: Consumer Price Index reflects the state in general economy,
    so calculating the correlation between it and price could give us the insights of price behaviour
    """

    return -correlation(ts_ffill(s.lme_close_price), ts_ffill(s.lme_us_cpi))
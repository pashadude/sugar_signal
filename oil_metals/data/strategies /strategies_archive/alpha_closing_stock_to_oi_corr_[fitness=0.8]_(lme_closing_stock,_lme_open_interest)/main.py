config = AlphaConfig(assets = ['CMAL3', 'CMCU3', 'CMNI3', 'CMZN3'], start_date = '2021-10-20')
def alpha_closing_stock_to_oi_corr(
        s: Streams,
        window=18
) -> pd.DataFrame:
    """
    Hypothesis: Correlation between closing stock
    and open interest may give us the intuition of price behaviour
    """
    open_interest = ts_delay(s.lme_open_interest, 1)
    res = correlation(ts_ffill(s.lme_closing_stock), ts_ffill(open_interest), window)
    res = ts_mean(res, 5)

    return res
config = AlphaConfig()
def alpha_brent_corr_no_delay(
        s: Streams,
) -> pd.DataFrame:
    """
    Hypothesis: hypothesis is that brent crude oil is the potential predictor of the
    metal prices. Combining the stock & economic alpha we get better results.
    """
    res = brent_stock_out_corr(s) + brent_on_warrant_corr(s) + brent_fed_assets_corr(s)

    return res
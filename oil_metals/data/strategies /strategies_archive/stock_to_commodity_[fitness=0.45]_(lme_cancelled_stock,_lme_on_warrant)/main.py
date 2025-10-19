config = AlphaConfig()
def stock_to_commodity(s: Streams) -> pd.DataFrame:
    """
    Supply and demand. The cancelled stocks are those metals that have earmarked for withdraw from warehouses.
    They are no longer available for trading. An increase in cancelled stocks could suggest that rising demand for physical delivery (immediate)
    therefore potentially bullish for the market. We calculate the ratio between cancelled stocks and on-warrant stocks (results are similar).
    We take log since the ratio is not normally distributed.
    """
    scores =s.lme_cancelled_stock/s.lme_on_warrant
    scores = np.log(scores)
    scoring_halflife=252
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=True,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params)
    return scores
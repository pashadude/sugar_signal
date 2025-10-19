config = AlphaConfig()
def dollar_to_commodity(s:Streams) -> pd.DataFrame:
    # Dollar to Commodity
    # Possible improvement: However, the current performance is bit disappointing.
    # We could use regression for future improvement
    input_data = s.lme_us_doll_ind
    returns = input_data.pct_change()
    short_window=84
    long_window=252
    scores = moving_average_crossover(returns, short_window, long_window).pipe(smooth_data, 5)

    compute_realized_volatility(returns, halflife=84)

    scoring_params = dict(mean_halflife=252*3,
                          volatility_halflife=252*3,
                          subtract_mean=False,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params)*-1
    return scores
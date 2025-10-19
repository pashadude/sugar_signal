config = AlphaConfig()
def simple_momentum_conditional_on_volatility(s: Streams) -> pd.DataFrame:
    # short-term momentum, overlay with volatility filter
    input_data = s.lme_close_price.pct_change()
    calculate_averaging_halflife = 21
    scoring_halflife = 252
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=False,
                          cap=2)

    scores = input_data.pipe(smooth_data, calculate_averaging_halflife).pipe(compute_z_score, **scoring_params).ffill(limit=5)
    scores = scores.sub(scores.mean(axis=1), axis=0)


    volatility_window=5
    calculate_averaging_window=3
    realised_volatility_scoring_params = dict(mean_halflife=252, volatility_halflife=252*3, subtract_mean=True, cap=2)
    volatility_environment = create_volatility_regime(input_data, volatility_window,
                                                      calculate_averaging_window,realised_volatility_scoring_params,
                                                      threshold=3/10, replacement_score=np.nan)
    scores = scores.mul(volatility_environment)
    scores = scores.pipe(smooth_data, 5)
    return scores
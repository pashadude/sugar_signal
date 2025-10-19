config = AlphaConfig()
def skewness_overlay_with_volatility(s: Streams) -> pd.DataFrame:
    """
    Skenwess overlay with Volatility. RV strategy
    """
    # close on close
    input_data = s.lme_close_price.pct_change()
    calculate_averaging_halflife = 5
    window_length = 63
    scoring_halflife = 21*12

    input_data = input_data.pipe(smooth_data, halflife=calculate_averaging_halflife)
    scores = input_data.rolling(window=window_length).skew()
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=True,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params)
    scores = scores.sub(scores.mean(axis=1), axis=0)
    volatility_window=5
    calculate_averaging_window=3

    # calculate volatility window
    realised_volatility_scoring_params = dict(mean_halflife=252, volatility_halflife=252*3, subtract_mean=True, cap=2)
    # we can move threshold to lower number.
    volatility_environment = create_volatility_regime(input_data, volatility_window,
                                                             calculate_averaging_window, realised_volatility_scoring_params,
                                                             threshold=0.5/10, replacement_score=np.nan)
    # risk on risk off
    scores = scores.mul(volatility_environment)
    return scores
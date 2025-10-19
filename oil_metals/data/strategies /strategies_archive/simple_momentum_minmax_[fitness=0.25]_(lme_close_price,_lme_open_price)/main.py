config = AlphaConfig()
def simple_momentum_minmax(s: Streams) -> pd.DataFrame:
    """
    Using Min-Max to Trade RV.
    Logic: Using Rolling min and Rolling max to determine the trend
    """
    # close on close
    # input_data = s.lme_close_price/s.lme_open_price-1
    input_data = s.lme_close_price
    calculate_averaging_halflife = 1
    window_length = 63
    scoring_halflife = 5

    input_data = input_data.pipe(smooth_data, halflife=calculate_averaging_halflife)
    metric_series = (input_data.shift(1).rolling(window_length).min() + input_data.shift(1).rolling(
        window_length).max()) / 2
    scores = input_data.div(metric_series) - 1
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=False,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params)
    # remove the mean
    scores = scores.sub(scores.mean(axis=1), axis=0)
    scores = scores.pipe(smooth_data, 5).clip(-2, 2)
    return scores
config = AlphaConfig()
def economic_condition_to_commodity(s: Streams) -> pd.DataFrame:
    """
    Similar to VIX-Yield Curve cycles. We use front (fed_rate) instead of yield curve.
    Based on the paper: Predicting Recession Using VIX-Yield Curve Cycles.
    Delaying date by a month
    """
    scores = s.lme_us_fed_rate.ffill()/s.lme_us_vix
    scoring_halflife=63
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=True,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params)*-1
    return scores
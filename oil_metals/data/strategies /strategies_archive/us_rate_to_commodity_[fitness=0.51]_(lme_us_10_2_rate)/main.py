config = AlphaConfig()
def us_rate_to_commodity(s: Streams) -> pd.DataFrame:
    """
    US interest rate. 10y - 2y. A key indicator.
    An increase in spread, relative to its own history, suggests that the curve is steeping (accelerating) and a
    acceleration in economic actives -> higher commodity price. Vice versa.
    We can either do 63 days (3m) or 252 days (1y). 63m reacts slightly faster to the policy change.
    """
    scores = s.lme_us_10_2_rate
    scoring_halflife = 63
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=True,
                          cap=2)

    scores = scores.pipe(compute_z_score, **scoring_params)
    return scores
config = AlphaConfig()
def us_vix(s: Streams) -> pd.DataFrame:
    """
    VIX
    Rationale: Check the VIX trend. The higher the VIX daily return (vs. its own history),
    the worst the market risk-sentiment. Commodities are considered risky assets.
    Use first difference instead of the absolute values.

    """
    # close on close
    input_data = s.lme_us_vix.diff()
    scores = input_data.astype('float')
    scoring_halflife = 252
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=False,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params).pipe(smooth_data, 5)*-1
    return scores
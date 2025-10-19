config = AlphaConfig()
def brent_oil_to_commodity(s:Streams) -> pd.DataFrame:
    # Assumption
    # Brent crude is a key component in inflation estimation so the higher the brent crude, the higher the inflation
    # However, a better way to construct the signal is to use the curve and we should explore it in the future
    # We could also do a seasonal adjustment in the future version
    # additionally we could add gas-oil and others in the future version
    half_life=10
    scores = s.lme_brent_oil.pct_change().pipe(smooth_data, halflife=half_life)
    scoring_halflife=half_life
    scoring_params = dict(mean_halflife=scoring_halflife,
                          volatility_halflife=scoring_halflife,
                          subtract_mean=False,
                          cap=2)
    scores = scores.pipe(compute_z_score, **scoring_params)
    return scores
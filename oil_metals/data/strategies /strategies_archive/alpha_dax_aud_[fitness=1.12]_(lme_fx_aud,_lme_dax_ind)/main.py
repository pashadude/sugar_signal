config = AlphaConfig()
def alpha_dax_aud(s, lookback=63) -> pd.DataFrame:
    """
    Thesis:
        The DAX index (Germany’s leading equity benchmark) can act as a proxy for global
        industrial activity due to Germany’s large export-driven manufacturing sector.
        The Australian dollar (AUD) represents expectations for commodity prices because 
        Australia is a major exporter of key raw materials.

        By taking the ratio DAX/AUD:
          - A rising ratio suggests that equity markets are discounting stronger global
            industrial activity (lifting DAX) relative to how much commodity price
            optimism is baked into the AUD.
          - If the AUD lags behind, it may indicate that commodity markets have yet to
            fully “catch up” to expectations implied by stronger industrial demand.
          - This can signal a bullish setup for base metals, because rising industrial
            demand typically increases demand for raw materials.

    """

    # Step 1: Retrieve and forward-fill data for DAX and AUD
    dax = ts_ffill(s.lme_dax_ind)
    aud = ts_ffill(s.lme_fx_aud)

    # Step 2: Compute the ratio (DAX / AUD)
    ratio = dax / aud

    # Take the log of the ratio for variance stabilization
    ratio = np.log(ratio)

    # Step 3: Apply a rolling/z-score normalization
    scoring_params = dict(
        mean_halflife=lookback,
        volatility_halflife=lookback,
        subtract_mean=True,
        cap=2  # Caps extreme values in the z-score
    )
    normalized_signal = ratio.pipe(compute_z_score, **scoring_params)

    # Return the final z-scored signal
    return normalized_signal
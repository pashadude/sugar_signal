config = AlphaConfig()
def alpha_cny_pmi_fx(s, lookback=63) -> pd.DataFrame:
    """
    Thesis:
        The China Purchasing Managers’ Index (PMI) reflects China's manufacturing
        activity: rising PMI indicates stronger industrial demand.
        The USD/CNY exchange rate captures the yuan’s strength
        against the US dollar; a stronger yuan (lower USD/CNY) makes US dollar–
        priced commodities more affordable for Chinese buyers.

        By taking the ratio PMI / USD/CNY:
          - A rising ratio suggests that China’s manufacturing demand is improving
            (higher PMI) and/or the yuan is strengthening (lower USD/CNY)—both of
            which is supportive base metals prices.
          - A falling ratio indicates weakening manufacturing momentum and/or
            yuan depreciation, typically bearish for base metals.
    """

    # Step 1: Retrieve and forward-fill data for China PMI and USD/CNY
    cny_pmi = ts_ffill(s.lme_cn_pmi)
    cny_fx = ts_ffill(s.lme_fx_cny)

    # Step 2: Compute the ratio (China PMI / USD/CNY)
    ratio = cny_pmi / cny_fx

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
config = AlphaConfig()
def us_real_rate_signal(s: Streams, lookback=63) -> pd.DataFrame:
    """
    Thesis:
    The relationship between the US Federal Funds Rate and inflation reflects the real interest rate,
    which significantly impacts economic activity and base metal prices. 

    - When the Federal Funds Rate is higher than inflation (positive real rate), US monetary policy is 
      restrictive, slowing the economy and creating headwinds for base metal prices.
    - When the Federal Funds Rate is below inflation (negative real rate), US monetary policy is stimulative,
      supporting economic growth and boosting base metal prices.

    This alpha function generates a continuous signal to measure the real rate's impact on base metal prices.

    """

    # Step 1: Forward-fill missing values for inflation and Federal Funds Rate
    us_inflation_true = ts_ffill(s.lme_trufl_infl_us)
    fed_rate = ts_ffill(s.lme_us_fed_rate)

    # Step 2: Compute the real rate ratio
    real_rate_ratio = fed_rate / us_inflation_true

    # Step 3: Apply z-score normalization
    scoring_params = dict(
        mean_halflife=lookback,
        volatility_halflife=lookback,
        subtract_mean=True,
        cap=2  # Limit extreme values
    )
    normalized_signal = real_rate_ratio.pipe(compute_z_score, **scoring_params)

    # Step 4: Invert the signal to align with the hypothesis
    final_signal = normalized_signal * -1

    return final_signal
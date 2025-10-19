config = AlphaConfig(neutralization = 'market')
def alpha_lme_intra_metal_corr(
    s: Streams,
    pct_change_period: int = 5,
    smooth_period: int = 63,
    corr_window: int = 21
) -> pd.DataFrame:
    """
    Hypothesis
    ----------
    1) On-warrant inventory drops (negative pct_change) → bullish signal.
    2) If a metal's price returns are highly correlated with the rest of the complex,
       we reduce that metal's signal (because unique supply/demand info might be overshadowed).

    Logic
    -----
    1) Smooth LME on-warrant inventories over 'smooth_period' days.
    2) Compute 'pct_change_period'-day % change, then invert it (negative => bullish if inventory falls).
       Take log(...) to compress extremes.
    3) Compute rolling correlation of each metal's daily returns vs. the average returns
       of all other metals over 'corr_window' days.
    4) Scale the base signal by (1 - correlation). Higher correlation => smaller final signal.

    Returns
    -------
    A DataFrame (dates × metals) of final signals.
    """

    # Step 1: Base Signal from LME On-Warrant
    lme_ow_smoothed = ts_mean(s.lme_on_warrant, smooth_period)  # smooth on-warrant data
    pct_change_data = lme_ow_smoothed.pct_change(pct_change_period)  # multi-day % change
    raw_signal = -pct_change_data                                   # negative => bullish if inventory fell
    raw_signal = np.log(raw_signal.clip(lower=1e-9))                # log-transform to manage outliers

    # Step 2: Rolling Correlation vs. "Rest of LME Base Metal Complex"
    daily_ret = s.lme_close_price.pct_change()
    metals = s.lme_close_price.columns
    corr_df = pd.DataFrame(index=daily_ret.index, columns=metals, dtype=float)

    for metal in metals:
        # 1) Compute mean return of OTHER metals
        other_metals = [m for m in metals if m != metal]
        rest_mean_ret = daily_ret[other_metals].mean(axis=1)

        # 2) Rolling correlation: this metal vs. rest_mean_ret
        corr_df[metal] = (
            daily_ret[metal]
            .rolling(corr_window)
            .corr(rest_mean_ret)
        )

    # Step 3: Continuous downweight factor based on correlation
    #    correlation ∈ [-1, +1] => factor = (1 - corr)
    #    higher corr => smaller factor => smaller final signal
    factor = (1 - corr_df)

    # Step 4: Combine base signal with correlation factor
    final_signal = raw_signal * factor

    return final_signal
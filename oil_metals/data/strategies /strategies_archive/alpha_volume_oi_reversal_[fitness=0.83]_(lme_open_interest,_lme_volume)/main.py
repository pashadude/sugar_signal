config = AlphaConfig()
def alpha_volume_oi_reversal(
        s: Streams,
        window=60,
):
    """
    Hypothesis: Current alpha is based on Quantpedia paper called "Short Term Reversal with Futures".
    Unfortunately, short-term strategy didn't work, so the window is set to 60 days and some additional
    parameter tuning and smoothing applied.
    Periods were split into high/low volume and high/low open interest.
    Then go long, if high volume & low oi and vice versa.
    """
    volume = s.lme_volume
    open_interest = s.lme_open_interest

    # Detrend volume by dividing by the sample mean
    detrended_volume = volume / ts_mean(volume, window)

    # Calculate volume and open interest changes
    vol_change = delta(detrended_volume, window)
    oi_change = delta(open_interest, window)

    # Determine mean changes
    mean_vol_change = ts_mean(vol_change, window)
    mean_oi_change = ts_mean(oi_change, window)

    # Define groups based on high/low volume and high/low open interest
    high_volume = vol_change > mean_vol_change
    low_volume = ~high_volume
    high_open_interest = oi_change > mean_oi_change
    low_open_interest = ~high_open_interest

    # Filter contracts into high-volume & low-open-interest groups
    res = volume.copy()
    res[:] = 0
    res[high_volume & low_open_interest] = 2
    res[low_volume & high_open_interest] = -5

    # Smooth and trim the values
    res = ts_mean(res, 10)
    res = ts_clip(res, -2, 2)

    return res
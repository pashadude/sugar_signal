config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def volume_to_oi_ratio_change(s: Streams, window=10):
    """Percentage change in the Volume to Open Interest ratio."""
    vol = ts_mean(s.lme_volume, window)
    oi = ts_mean(s.lme_open_interest, window)
    ratio = vol / oi
    result = ratio.pct_change(window)

    return -result
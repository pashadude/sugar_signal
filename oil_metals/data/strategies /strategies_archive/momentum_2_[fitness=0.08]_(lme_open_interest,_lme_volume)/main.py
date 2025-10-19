config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def momentum_2(s: Streams, window=7, ts_delay_flag=True, standardise=True):
    """Momentum dynamics in Volume and Open Interest."""
    result = s.lme_volume.pct_change(window) * s.lme_open_interest.pct_change(window)
    if standardise:
        result = zscore(result)
    if ts_delay_flag:
        result = ts_delay(result, 2)
    return -result
config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def momentum_3(s: Streams, window=7, ts_delay_flag=False, standardise=True):
    """Momentum of Volume and OI."""
    result = s.lme_volume.diff(window) * s.lme_open_interest.diff(window)
    if standardise:
        result = zscore(result)
    if ts_delay_flag:
        result = ts_delay(result)
    return -result
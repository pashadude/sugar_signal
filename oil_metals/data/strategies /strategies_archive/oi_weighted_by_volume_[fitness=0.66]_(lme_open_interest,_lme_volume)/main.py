config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def oi_weighted_by_volume(s: Streams, ts_delay_flag=False, standardise=True):
    """Open Interest weighted by Volume."""
    vol = ts_mean(s.lme_volume)
    oi = ts_mean(s.lme_open_interest)
    result = oi * vol / ts_sum(vol)
    if standardise:
        result = zscore(result)
    if ts_delay_flag:
        result = ts_delay(result)
    return result
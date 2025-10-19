config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def rolling_corr(s: Streams, window=7, ts_delay_flag=False):
    """Rolling correlation"""
    result = s.lme_volume.rolling(window).corr(s.lme_open_interest)
    if ts_delay_flag:
        result = ts_delay(result)
    return result
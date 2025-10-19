config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_7(s: Streams, standardise=True):
    """Normalised signal."""
    oi = ts_mean(s.lme_open_interest)
    vol = ts_mean(s.lme_volume)
    result = (oi - oi.mean()) / oi.std() + (vol - vol.mean()) / vol.std()
    if standardise:
        result = zscore(result)
    return result
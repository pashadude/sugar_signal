config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def volume_to_oi_alignment(s: Streams, ts_delay_flag=False, standardise=True):
    """Alignment between market activity (volume) and market commitment (open interest)."""
    result = np.sign(s.lme_volume.diff()) * np.sign(s.lme_open_interest.diff())
    if standardise:
        result = zscore(result)
    if ts_delay_flag:
        result = ts_delay(result)
    return -result
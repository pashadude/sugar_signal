config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_volume_spike(s: Streams, window=5):
    recent_mean_vol = ts_mean(s.lme_volume, window=window)
    # Positive if current volume > recent mean volume
    return s.lme_volume - recent_mean_vol
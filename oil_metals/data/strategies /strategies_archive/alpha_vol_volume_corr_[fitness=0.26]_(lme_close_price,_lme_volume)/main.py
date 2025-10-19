config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_vol_volume_corr(s: Streams, window=7):
    vol = ts_stddev(s.lme_close_price, window=window)
    vol_vol_corr = correlation(vol, s.lme_volume, window=window)
    return vol_vol_corr
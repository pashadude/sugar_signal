config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def volume_oi_rsi_slower(s: Streams, window=21):
    """
    RSI over 21 days instead of 14. 
    Slows down the RSI reaction to small moves and reduces whipsaws.
    """
    vol = ts_mean(s.lme_volume)
    oi = ts_mean(s.lme_open_interest)
    delta_volume = delta(vol)
    delta_oi = delta(oi)

    gain_volume = ts_mean(delta_volume.where(delta_volume > 0, 0), window=window)
    loss_volume = ts_mean(-delta_volume.where(delta_volume < 0, 0), window=window)
    rs_volume = gain_volume / loss_volume
    rsi_volume = 100 - (100 / (1 + rs_volume))

    gain_oi = ts_mean(delta_oi.where(delta_oi > 0, 0), window=window)
    loss_oi = ts_mean(-delta_oi.where(delta_oi < 0, 0), window=window)
    rs_oi = gain_oi / loss_oi
    rsi_oi = 100 - (100 / (1 + rs_oi))

    result = rsi_volume - rsi_oi
    return -result
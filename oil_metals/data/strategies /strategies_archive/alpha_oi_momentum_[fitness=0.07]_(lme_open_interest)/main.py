config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_oi_momentum(s: Streams, window=5):
    # Positive if OI is increasing
    return -delta(s.lme_open_interest, period=window)
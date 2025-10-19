config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_recent_price_momentum(s: Streams, window=5):
    recent_mean_price = ts_mean(s.lme_close_price, window=window)
    # Positive if current price > recent mean
    return -s.lme_close_price - recent_mean_price
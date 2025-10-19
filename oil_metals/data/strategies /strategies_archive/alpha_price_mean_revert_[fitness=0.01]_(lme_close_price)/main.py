config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_price_mean_revert(s: Streams, window=5):
    mean_price = ts_mean(s.lme_close_price, window=window)
    # Positive if price < mean (go long expecting revert), negative if price > mean (go short)
    return mean_price - s.lme_close_price
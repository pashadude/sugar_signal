config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_price_range_expansion(s: Streams, window=5):
    recent_range = (s.lme_high_price - s.lme_low_price)
    # Compare current range to its recent average
    return recent_range - ts_mean(recent_range, window=window)
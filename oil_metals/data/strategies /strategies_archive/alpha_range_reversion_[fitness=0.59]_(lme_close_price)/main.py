config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_range_reversion(s: Streams, window=5):
    recent_min = ts_min(s.lme_close_price, window=window)
    recent_max = ts_max(s.lme_close_price, window=window)
    # Normalize current price between 0 and 1
    norm_price = safe_div(s.lme_close_price - recent_min, (recent_max - recent_min))
    # Expect mean reversion: high norm_price => go short, low norm_price => go long
    return 0.5 - norm_price
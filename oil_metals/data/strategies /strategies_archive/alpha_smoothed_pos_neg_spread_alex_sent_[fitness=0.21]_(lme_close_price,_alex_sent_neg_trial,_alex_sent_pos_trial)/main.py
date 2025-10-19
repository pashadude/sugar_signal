config = AlphaConfig(booksize = 10000000.0, end_date = '2024-05-31', neutralization = 'market')
def alpha_smoothed_pos_neg_spread_alex_sent(s, window=10):
    """
    Correlation of price with exponential smoothing of (pos - neg).
    """
    pos_neg_spread = s.alex_sent_pos_trial - s.alex_sent_neg_trial
    smoothed_spread = ts_ewm(pos_neg_spread, span=window)
    return -correlation(s.lme_close_price, smoothed_spread, window=window)
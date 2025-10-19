config = AlphaConfig(booksize = 10000000.0, end_date = '2024-05-31', neutralization = 'market')
def alpha_smoothed_neutral_alex_sent(s, window=20):
    """
    Rolling mean of neutral sentiment confidence, then correlation with price.
    """
    neut_conf_smooth = ts_mean(s.alex_sent_neut_conf_trial, window)
    return -correlation(s.lme_close_price, neut_conf_smooth, window=window)
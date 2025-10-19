config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_price_zscore_revert(s: Streams, window=30):
    # zscore automatically subtracts mean and divides by std over the window
    price_z = zscore(s.lme_close_price, window=window)
    # Invert the z-score so positive indicates going long when price is below mean, negative when price is above mean
    return -price_z
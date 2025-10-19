config = AlphaConfig(neutralization = 'market')
def alpha_sma20_sma50_n_close_sma20_diff(s: Streams):
    ## Normalization ###
    close_price = s.lme_close_price
    close_price = zscore(close_price, window=10)
    ### SMAs Computations ###
    SMA8_close_price = ts_mean(close_price, 8)
    SMA20_close_price = ts_mean(close_price, 20)
    SMA50_close_price = ts_mean(close_price, 50)
    SMA200_close_price = ts_mean(close_price, 200)
    """
    Hypothesis: If the short-term trend (SMA20) is above the long-term trend (SMA50) and the current price (s.lme_close_price) is above the SMA20,
    it indicates upward momentum, and vice versa for downward momentum [normalized close prices].
    """
    return (SMA20_close_price - SMA50_close_price) + (close_price - SMA20_close_price)
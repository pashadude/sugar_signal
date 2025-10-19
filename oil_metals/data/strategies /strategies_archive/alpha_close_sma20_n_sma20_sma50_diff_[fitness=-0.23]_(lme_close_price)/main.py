config = AlphaConfig(neutralization = 'market')
def alpha_close_sma20_n_sma20_sma50_diff(s: Streams):
    ## Normalization ###
    close_price = s.lme_close_price
    close_price = zscore(close_price, window=10)
    ### SMAs Computations ###
    SMA8_close_price = ts_mean(close_price, 8)
    SMA20_close_price = ts_mean(close_price, 20)
    SMA50_close_price = ts_mean(close_price, 50)
    SMA200_close_price = ts_mean(close_price, 200)
    """
    Hypothesis: Short-term momentum with Alignment of Moving Averages predicts price trends.
    """
    return (close_price - SMA20_close_price) + (SMA20_close_price - SMA50_close_price)
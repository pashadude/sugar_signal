config = AlphaConfig(neutralization = 'market')
def alpha_sma20_sma50_n_close_sma50_diff(s: Streams):
    ## Normalization ###
    close_price = s.lme_close_price
    close_price = zscore(close_price, window=10)
    ### SMAs Computations ###
    SMA8_close_price = ts_mean(close_price, 8)
    SMA20_close_price = ts_mean(close_price, 20)
    SMA50_close_price = ts_mean(close_price, 50)
    SMA200_close_price = ts_mean(close_price, 200)
    """
    Hypothesis: If the SMA20 and Close price are larger than the SMA50 respectively [normalized close prices],, it suggests an upward price momentum,
    If negative, it suggests a downward price momentum.
    """
    return (SMA20_close_price - SMA50_close_price) + (close_price - SMA50_close_price)
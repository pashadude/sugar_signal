config = AlphaConfig(neutralization = 'market')
def alpha_sma8_sma50_n_close_sma20_diff(s: Streams):
    ## Normalization ###
    close_price = s.lme_close_price
    close_price = zscore(close_price, window=10)
    ### SMAs Computations ###
    SMA8_close_price = ts_mean(close_price, 8)
    SMA20_close_price = ts_mean(close_price, 20)
    SMA50_close_price = ts_mean(close_price, 50)
    SMA200_close_price = ts_mean(close_price, 200)
    """
    Hypothesis: Domination of short-term normalized prices over medium-term normalized prices leads to positive alpha
    and indicating upward momentum, and negative alpha indicates downward momentum.
    """
    return (SMA8_close_price - SMA50_close_price) + (close_price - SMA20_close_price)
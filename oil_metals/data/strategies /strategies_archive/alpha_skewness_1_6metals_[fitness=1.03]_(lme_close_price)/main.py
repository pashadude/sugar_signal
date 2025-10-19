config = AlphaConfig(neutralization = 'market')
def alpha_skewness_1_6metals(
        s: Streams,
):
    """
    Hypothesis: Calculate the skewness for commodity prices.
    Then short ones with big value and go long with ones that have small value of skewness
    """
    T = 90
    data = ts_ffill(s.lme_close_price)
    returns = ts_pct_change(data)
    average_returns = ts_mean(returns, T)
    sigma = ts_stddev(returns, T)
    skewness = ts_sum(ts_pow(returns - average_returns, 3), T) / (T * ts_pow(sigma, 3))

    return -skewness
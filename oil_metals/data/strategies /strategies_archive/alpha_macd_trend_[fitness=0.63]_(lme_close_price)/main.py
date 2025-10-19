config = AlphaConfig()
def alpha_macd_trend(
        s: Streams,
        window=5,
):
    """
    Hypothesis: Alpha based on "MACD Trend Following in Chinese Commodities" article on Quantpedia.
    If the histogram(H) H(t) < 0 & H(t-2) > 0, then Short;
    If H(t) > 0 & H(t-2) < 0, then Long.
    In addition, window 5 smoothing of the result.
    """
    short_window = 12
    long_window = 26
    signal_window = 9

    # Calculate EMA and MACD
    prices = ts_ffill(s.lme_close_price).copy()
    short_ema = ts_ewm(prices, span=short_window, adjust=False)
    long_ema = ts_ewm(prices, span=long_window, adjust=False)
    macd = short_ema - long_ema
    signal = ts_ewm(macd, span=signal_window, adjust=False)
    histogram = macd - signal

    # label the signal in the histogram
    labeled = histogram.copy()
    labeled[:] = 0
    labeled[(histogram < 0) & (ts_delay(histogram, 2) > 0)] = -1
    labeled[(histogram > 0) & (ts_delay(histogram, 2) < 0)] = 1

    # Smooth the result
    result = ts_mean(labeled, window)

    return result
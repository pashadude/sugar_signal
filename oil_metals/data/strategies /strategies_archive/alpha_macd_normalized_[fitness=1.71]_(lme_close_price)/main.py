config = AlphaConfig()
def alpha_macd_normalized(
        s: Streams,
        window=10,
        normalized_window=60
):
    """
    Hypothesis: the same logic as behind the MACD indicator,
    but histogram values are normalized by price levels and zscore'd
    """
    short_window = 12
    long_window = 30
    signal_window = 12

    df = ts_ffill(s.lme_close_price).copy()

    short_ema = ts_ewm(df, span=short_window, adjust=False)
    long_ema = ts_ewm(df, span=long_window, adjust=False)
    macd = short_ema - long_ema
    signal = ts_ewm(macd, span=signal_window, adjust=False)
    histogram = macd - signal

    histogram = ts_mean(histogram, window) / ts_mean(df, window)
    histogram_normalized = zscore(histogram, normalized_window)
    histogram_normalized = -ts_mean(histogram_normalized, window)

    return histogram_normalized
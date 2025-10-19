config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_rsi_contrarian_smooth(s: Streams, window=14, smooth_window=5, rsi_upper=70, rsi_lower=30):
    """
    RSI-based contrarian approach with smoothing and thresholds.
    - RSI > rsi_upper => short
    - RSI < rsi_lower => long
    - else 0
    """
    rsi_vals = ts_rsi(s.lme_close_price)
    rsi_smooth = ts_mean(rsi_vals, window=smooth_window)

    # Initialize signal as 0
    signal = pd.DataFrame(0.0, index=rsi_smooth.index, columns=rsi_smooth.columns)

    # Short condition
    cond_short = (rsi_smooth > rsi_upper)
    signal = ts_where(signal, ~cond_short, other=-1.0)

    # Long condition
    cond_long = (rsi_smooth < rsi_lower)
    signal = ts_where(signal, ~cond_long, other=1.0)

    return signal
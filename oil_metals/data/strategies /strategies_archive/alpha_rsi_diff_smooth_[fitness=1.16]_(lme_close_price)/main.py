config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_rsi_diff_smooth(s: Streams, rsi_window=10, smooth_window=10):
    """
    RSI-based signal that compares RSI to the neutral line (50),
    then smooths the difference over 'smooth_window' days.
    Hypothesis:
      - If RSI is consistently above 50 (positive difference), bullish momentum.
      - If RSI is consistently below 50 (negative difference), bearish momentum.
    """
    rsi_vals = ts_rsi(s.lme_close_price, rsi_window)
    diff_from_50 = rsi_vals - 50.0
    # Smooth the difference to reduce turnover
    return -ts_mean(diff_from_50, window=smooth_window)
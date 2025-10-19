config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_2(s: Streams, window=7):
    """Hypothesis: Simple open interest momentum."""
    result = ts_mean(s.lme_open_interest, window).pct_change(window)
    return result
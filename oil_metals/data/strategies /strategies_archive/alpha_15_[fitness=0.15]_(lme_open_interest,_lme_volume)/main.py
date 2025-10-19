config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_15(s: Streams, window=7):
    """Hypothesis: OI & Volume momentum product."""
    vol = ts_mean(s.lme_volume, window)
    oi = ts_mean(s.lme_open_interest, window)
    result = oi.pct_change(window) * vol

    return result
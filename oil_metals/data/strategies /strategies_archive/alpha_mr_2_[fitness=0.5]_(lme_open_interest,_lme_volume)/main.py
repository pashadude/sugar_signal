config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_mr_2(s: Streams, window=21, standardise=False):
    """
    Mean reversion of the difference between Volume and OI.
    Hypothesis:
        - If Volume significantly exceeds OI, the market may be 'overheated' short-term.
        - If OI outstrips Volume, the market may be 'quiet' and likely to revert.
    """
    volume_smooth = ts_mean(s.lme_volume, window)
    oi_smooth = ts_mean(s.lme_open_interest, window)

    # Spread between Volume and OI
    spread = volume_smooth - oi_smooth

    # Deviate from its rolling average => revert
    spread_dev = spread - ts_mean(spread, window)

    # Negate for mean reversion (above average => short the spread, below => long the spread)
    result = -spread_dev

    if standardise:
        result = zscore(result)
    return result
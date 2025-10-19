config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_mr_cancel_warrant_decay1(s: Streams, window=14):
    """
    Hypothesis:
      - Compare Cancelled stock and On-warrant stock with a decaying weight on recent data.
      - If difference grows too large, it may revert.
    """
    cancel_smooth = ts_mean(s.lme_cancelled_stock, window)
    warrant_smooth = ts_mean(s.lme_on_warrant, window)

    # Weighted difference using ts_decay_exp_window (exponential weighting)
    diff = cancel_smooth - warrant_smooth
    diff_decay = ts_decay_exp_window(diff, window, factor=0.5)  # more weight on recent points

    # Compare to rolling mean => revert
    diff_mean = ts_mean(diff_decay, window)
    diff_dev = diff_decay - diff_mean

    result = -diff_dev
    return result
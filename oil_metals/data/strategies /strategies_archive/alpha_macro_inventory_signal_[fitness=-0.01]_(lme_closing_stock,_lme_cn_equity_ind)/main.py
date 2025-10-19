config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_macro_inventory_signal(s: Streams, window=5, standardise=True):
    cn_mom = ts_mean(s.lme_cn_equity_ind) - ts_mean(s.lme_cn_equity_ind, window=window)
    inv_change = delta(ts_mean(s.lme_closing_stock), period=window)
    # If CN improves (cn_mom > 0) and inventories fall (inv_change < 0), bullish
    result = cn_mom * (-inv_change)
    if standardise:
        result = zscore(result)
    return result
config = AlphaConfig()
def alpha_adj_corr_13(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_stock_in and lme_stock_out) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_stock_in), ts_ffill(s.lme_stock_out), window=18)
    rsi_corr = ts_rsi(corr, period=33)

    result = (rsi_corr < 30)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 70)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    adj_corr= ( corr * (result + result2) )

    return - adj_corr
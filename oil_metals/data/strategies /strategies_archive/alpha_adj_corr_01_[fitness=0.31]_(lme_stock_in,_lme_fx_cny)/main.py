config = AlphaConfig()
def alpha_adj_corr_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_fx_cny and lme_stock_in) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_fx_cny), ts_ffill(s.lme_stock_in), window=54)
    rsi_corr = ts_rsi(corr, period=17)

    result = (rsi_corr < 40)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 60)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    adj_corr= ( corr * (result + result2) )

    return -corr + adj_corr
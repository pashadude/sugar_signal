config = AlphaConfig()
def alpha_adj_corr_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_fx_cny and lme_us_indust_prod_ind) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_fx_cny), ts_ffill(s.lme_us_indust_prod_ind), window=73)
    rsi_corr = ts_rsi(corr, period=26)

    result = (rsi_corr < 10)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 90)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    adj_corr= ( corr * (result + result2) )

    return -corr -adj_corr
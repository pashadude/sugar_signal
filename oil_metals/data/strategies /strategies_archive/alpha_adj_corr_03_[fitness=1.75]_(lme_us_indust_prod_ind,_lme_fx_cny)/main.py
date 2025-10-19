config = AlphaConfig()
def alpha_adj_corr_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_fx_cny and lme_us_indust_prod_ind) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_fx_cny), ts_ffill(s.lme_us_indust_prod_ind), window=70)
    rsi_corr = ts_rsi(corr, period=29)

    result = (rsi_corr < 20)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 80)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    adj_corr= ( corr * (result + result2) )

    return -corr -adj_corr
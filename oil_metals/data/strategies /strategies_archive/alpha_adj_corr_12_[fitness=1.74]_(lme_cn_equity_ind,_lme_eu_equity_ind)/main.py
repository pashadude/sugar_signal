config = AlphaConfig()
def alpha_adj_corr_12(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_cn_equity_ind and lme_eu_equity_ind) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_cn_equity_ind), ts_ffill(s.lme_eu_equity_ind), window=70)
    rsi_corr = ts_rsi(corr, period=17)

    result = (rsi_corr < 30)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 70)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    adj_corr= ( corr * (result + result2) )

    return -adj_corr
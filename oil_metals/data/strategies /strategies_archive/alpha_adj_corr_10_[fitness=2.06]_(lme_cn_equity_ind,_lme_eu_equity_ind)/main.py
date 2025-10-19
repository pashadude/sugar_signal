config = AlphaConfig()
def alpha_adj_corr_10(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Adjusted correlation via RSI (lme_cn_equity_ind and lme_eu_equity_ind) with ts_ffill.
    """
    corr = correlation(ts_ffill(s.lme_cn_equity_ind), ts_ffill(s.lme_eu_equity_ind), window=71)
    rsi_corr = ts_rsi(corr, period=22)

    result = (rsi_corr < 40)
    result = ts_where(result, result == True, 0)
    result = ts_where(result, result != True, 1)

    result2 = (rsi_corr > 60)
    result2 = ts_where(result2, result2 == True, 0)
    result2 = ts_where(result2, result2 != True, -1)

    adj_corr= ( corr * (result + result2) )

    return - adj_corr
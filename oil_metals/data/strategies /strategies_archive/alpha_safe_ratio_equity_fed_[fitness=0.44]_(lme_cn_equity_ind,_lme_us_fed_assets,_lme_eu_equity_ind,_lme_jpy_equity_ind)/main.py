config = AlphaConfig()
def alpha_safe_ratio_equity_fed(s: Streams):
    """
    Hypothesis:
    Strong equity markets in the EU, Japan, and China, combined with a more accommodated U.S. monetary policy,
    may indicate heightened consumer and producer confidence, potentially driving increased demand for base metals and rising prices.
    """
    cn_equity_ma10 = ts_mean(s.lme_cn_equity_ind, window=week_2)
    jpy_equity_ma10 = ts_mean(s.lme_jpy_equity_ind, window=week_2)
    eur_equity_ma10 = ts_mean(s.lme_eu_equity_ind, window=week_2)
    fed_assets_ma10 = ts_mean(ts_ffill(s.lme_us_fed_assets), window=week_2)
    com_equity_ind = cn_equity_ma10 + jpy_equity_ma10 + eur_equity_ma10
    return correlation(com_equity_ind, fed_assets_ma10)
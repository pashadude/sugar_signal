config = AlphaConfig()
def alpha_stock_to_china_pmi(s: Streams, window=30) -> pd.DataFrame:
    """
    Hypothesis: Correlation between stock and China's PMI now
    substracting the correlation with shifted value of China PMI
    """

    res = -correlation(s.lme_closing_stock, ts_delay(ts_ffill(s.lme_cn_pmi), window), window)

    # add only when sure that there is no lookahead, it increases the fitness
    # res = res + correlation(s.lme_closing_stock, s.lme_cn_pmi.ffill(), window)

    return res
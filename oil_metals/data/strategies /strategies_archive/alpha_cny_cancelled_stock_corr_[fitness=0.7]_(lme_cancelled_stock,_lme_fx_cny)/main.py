config = AlphaConfig()
def alpha_cny_cancelled_stock_corr(
        s: Streams,
        window=10,
        clip_level=0.1
) -> pd.DataFrame:
    """
    Hypothesis: High correlation of CNY currency and cancelled metal stock might 
    indicate high China demand for commodity metals, therefore boosting prices up.
    """

    return correlation(s.lme_fx_cny, s.lme_cancelled_stock, window)
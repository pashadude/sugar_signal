config = AlphaConfig()
def alpha_2del_with_ffill_04(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta (lme_cn_gdp) vs delta (lme_cn_gdp), ts_ffill.
    """
    return delta(ts_ffill(s.lme_cn_gdp), period=6) - delta(ts_ffill(s.lme_cn_pmi),  period=9)
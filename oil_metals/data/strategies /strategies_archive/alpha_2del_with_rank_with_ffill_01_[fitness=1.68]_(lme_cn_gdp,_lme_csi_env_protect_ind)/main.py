config = AlphaConfig()
def alpha_2del_with_rank_with_ffill_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta (lme_csi_env_protect_ind) vs delta (lme_cn_gdp), ts_ffill, ts_rank
    """
    return delta(ts_rank(ts_ffill(s.lme_csi_env_protect_ind), window=9), period=9) - delta(ts_rank(ts_ffill(s.lme_cn_gdp), window=17), period=17)
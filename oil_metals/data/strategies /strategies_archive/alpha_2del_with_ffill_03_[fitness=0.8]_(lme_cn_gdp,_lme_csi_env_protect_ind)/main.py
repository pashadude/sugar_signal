config = AlphaConfig()
def alpha_2del_with_ffill_03(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Delta (lme_csi_env_protect_ind) vs delta (lme_cn_gdp), ts_ffill.
    """
    return delta(ts_ffill(s.lme_csi_env_protect_ind),  period=8) - delta(ts_ffill(s.lme_cn_gdp), period=4)
config = AlphaConfig()
def alpha_2corr_cnnonfer_metalind(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Corrected correlation, basis - lme_csi_non_fer_metal_ind.
    """
    return (correlation(s.lme_csi_non_fer_metal_ind, s.lme_eu_equity_ind, window=20) - correlation(s.lme_us_vix, s.lme_csi_non_fer_metal_ind, window=31))
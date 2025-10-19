config = AlphaConfig()
def alpha_2corr_cnmm_ind(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Corrected correlation, basis - lme_csi_metal_mining_ind.
    """
    return (correlation(s.lme_csi_metal_mining_ind, s.lme_eu_equity_ind, window=25) - correlation(s.lme_us_vix, s.lme_csi_metal_mining_ind, window=26))
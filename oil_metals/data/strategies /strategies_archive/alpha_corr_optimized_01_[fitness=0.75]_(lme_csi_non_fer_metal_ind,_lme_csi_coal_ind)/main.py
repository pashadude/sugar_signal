config = AlphaConfig()
def alpha_corr_optimized_01(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Correlation lme_csi_non_fer_metal_ind VS lme_csi_coal_ind, optimized 
    """
    ver1=ts_rank(s.lme_csi_non_fer_metal_ind, window=4)
    ver2=ts_rank(s.lme_csi_coal_ind, window=2)

    return ver1 - ver2
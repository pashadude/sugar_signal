config = AlphaConfig()
def alpha_stddev_mmind_bricftse(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_csi_metal_mining_ind and lme_ftse_bric_50_ind.
    """
    ver1=ts_stddev(s.lme_csi_metal_mining_ind, window=14)
    ver2=ts_stddev(s.lme_ftse_bric_50_ind, window=17)

    return ver1 - ver2
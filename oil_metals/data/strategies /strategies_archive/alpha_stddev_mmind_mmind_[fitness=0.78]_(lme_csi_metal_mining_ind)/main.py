config = AlphaConfig()
def alpha_stddev_mmind_mmind(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_csi_non_fer_metal_ind and lme_csi_non_fer_metal_ind.
    """
    ver1=ts_stddev(s.lme_csi_metal_mining_ind, window=21)
    ver2=ts_stddev(s.lme_csi_metal_mining_ind, window=22)

    return ver1 - ver2
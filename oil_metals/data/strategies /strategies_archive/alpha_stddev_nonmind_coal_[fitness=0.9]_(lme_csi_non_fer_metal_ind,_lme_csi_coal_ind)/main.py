config = AlphaConfig()
def alpha_stddev_nonmind_coal(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_csi_non_fer_metal_ind and lme_csi_coal_ind.
    """
    ver1=ts_stddev(s.lme_csi_non_fer_metal_ind, window=11)
    ver2=ts_stddev(s.lme_csi_coal_ind, window=10)

    return ver1 - ver2
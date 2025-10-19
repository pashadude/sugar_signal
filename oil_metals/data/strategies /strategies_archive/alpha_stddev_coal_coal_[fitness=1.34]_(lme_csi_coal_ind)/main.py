config = AlphaConfig()
def alpha_stddev_coal_coal(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_csi_coal_ind and lme_csi_coal_ind.
    """
    ver1=ts_stddev(s.lme_csi_coal_ind, window=14)
    ver2=ts_stddev(s.lme_csi_coal_ind, window=11)

    return ver1 - ver2
config = AlphaConfig()
def alpha_stddev_coal_gas(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_csi_coal_ind and lme_gas_oil1.
    """
    ver1=ts_stddev(s.lme_csi_coal_ind, window=5)
    ver2=ts_stddev(s.lme_gas_oil1, window=13)

    return ver1 - ver2
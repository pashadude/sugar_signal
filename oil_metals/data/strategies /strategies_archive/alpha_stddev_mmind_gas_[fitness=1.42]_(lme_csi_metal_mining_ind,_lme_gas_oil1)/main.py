config = AlphaConfig()
def alpha_stddev_mmind_gas(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_csi_non_fer_metal_ind and lme_gas_oil1.
    """
    ver1=ts_stddev(s.lme_csi_metal_mining_ind, window=15)
    ver2=ts_stddev(s.lme_gas_oil1, window=14)

    return ver1 - ver2
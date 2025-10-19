config = AlphaConfig()
def alpha_stddev_bricftse_gas(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_ftse_bric_50_ind and lme_gas_oil1.
    """
    ver1=ts_stddev(s.lme_ftse_bric_50_ind, window=22)
    ver2=ts_stddev(s.lme_gas_oil1, window=10)

    return ver1 - ver2
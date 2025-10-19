config = AlphaConfig()
def alpha_stddev_gas_gas(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Patterns of standard deviation in different optimized timeframes: lme_gas_oil1 and lme_gas_oil1.
    """
    ver1=ts_stddev(s.lme_gas_oil1, window=21)
    ver2=ts_stddev(s.lme_gas_oil1, window=20)

    return ver1 - ver2
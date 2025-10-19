config = AlphaConfig()
def alpha_dep_zn(s: Streams):
    """
    Hypothesis: Positive values of deposits held by depository institutions at the Federal Reserve
    may indicate potential expansion in lending to businesses, stimulating economic activity
    and driving increased demand for base metals, leading to price growth. Conversely, negative values suggest the opposite effect.
    """
    dep_instit = ts_ffill(s.lme_us_dep_instit)
    dep_instit_zn = zscore(dep_instit, window=week_3)
    return dep_instit_zn
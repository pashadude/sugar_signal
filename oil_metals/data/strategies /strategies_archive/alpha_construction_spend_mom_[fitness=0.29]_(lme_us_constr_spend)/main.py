config = AlphaConfig()
def alpha_construction_spend_mom(s:Streams):
    """
    Hypothesis: Construction spending momentum reflects demand trends for base metals: rising momentum suggests increased demand,
    while falling momentum indicates declining base metal demand and pricing.
    """
    const_spend = ts_ffill(s.lme_us_constr_spend)
    const_spend_3mma = ts_mean(const_spend, window=quarterly)
    const_spend_6mma = ts_mean(const_spend, window=half)
    const_spend_mom = const_spend_6mma - const_spend_3mma
    const_spend_mom_zn = zscore(const_spend_mom, window=month_2)
    return ts_mean(const_spend_mom_zn, window=month_2)
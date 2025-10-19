config = AlphaConfig()
def alpha_construction_spend_growth_rate(s:Streams):
    """
    Hypothesis: Quarterly growth in U.S. construction spending indicates increased infrastructure investments
    and robust economic activity. This heightened demand for base metals reduces storage costs, potentially leading to a drop in their prices.
    """
    const_spend = ts_ffill(s.lme_us_constr_spend)
    construction_spend_growth = safe_div(delta(const_spend, period=quarterly), ts_delay(const_spend, period=quarterly))
    return - zscore(construction_spend_growth, window=quarterly)
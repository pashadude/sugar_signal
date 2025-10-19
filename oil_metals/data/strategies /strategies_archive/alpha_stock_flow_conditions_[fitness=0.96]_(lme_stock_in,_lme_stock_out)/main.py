config = AlphaConfig(neutralization = 'market')
def alpha_stock_flow_conditions(s: Streams, ma_window=63) -> pd.DataFrame:
    """
    Hypothesis:
    - If outflows dominate inflows (s_out_mean > s_in_mean), the market is tightening,
      and large outflows drive prices higher.
    - If inflows dominate outflows (s_in_mean > s_out_mean), the market is loosening,
      and large inflows drive prices lower.

    Method:
    - Compute rolling means and maxima for stock inflows and outflows.
    - Apply conditional logic to focus on the relevant driver (big outflows or big inflows).
    """

    # 1) Compute Rolling Means and Maxima
    s_out_mean = ts_mean(s.lme_stock_out, ma_window)
    s_out_max = ts_max(s.lme_stock_out, ma_window)
    s_in_mean = ts_mean(s.lme_stock_in, ma_window)
    s_in_max = ts_max(s.lme_stock_in, ma_window)

    # 2) Conditional Logic for res
    res = safe_div(s_out_max, s_in_mean).where(s_out_mean > s_in_mean, safe_div(s_out_mean, s_in_max))


    return res
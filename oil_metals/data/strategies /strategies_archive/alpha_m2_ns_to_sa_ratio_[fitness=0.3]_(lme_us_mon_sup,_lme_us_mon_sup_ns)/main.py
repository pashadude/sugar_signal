config = AlphaConfig()
def alpha_m2_ns_to_sa_ratio(s:Streams):
    """
    Hypothesis: The Wider gap between seasonally adjusted and seasonally unadjusted money supply (M2)
    reflects stronger monetary policy from the Federal Reserve, resulting in inflation growth and steady rise of base metals' prices.
    """
    m2 = ts_ffill(s.lme_us_mon_sup)
    m2_3mma = ts_mean(m2, window=quarterly)
    m2_ns = ts_ffill(s.lme_us_mon_sup_ns)
    m2_ns_3mma = ts_mean(m2_ns, window=quarterly)
    return safe_div(m2_ns_3mma, m2_3mma)
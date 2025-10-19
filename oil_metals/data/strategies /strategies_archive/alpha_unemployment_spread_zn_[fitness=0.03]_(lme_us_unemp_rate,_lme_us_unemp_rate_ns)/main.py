config = AlphaConfig()
def alpha_unemployment_spread_zn(s:Streams):
    """
    Hypothesis: Labor supply deficit may encourage the posting of non-seasonal vacancies over seasonal ones,
    reflecting normalization on the labor market and stronger economy potentially driving an increase in base metals' prices.
    """
    tur = ts_ffill(s.lme_us_unemp_rate)
    tur_2mma = ts_mean(tur, window=month_2)
    tur_ns = ts_ffill(s.lme_us_unemp_rate_ns)
    tur_ns_2mma = ts_mean(tur_ns, window=month_2)
    return zscore(tur_2mma - tur_ns_2mma, window=month_2)
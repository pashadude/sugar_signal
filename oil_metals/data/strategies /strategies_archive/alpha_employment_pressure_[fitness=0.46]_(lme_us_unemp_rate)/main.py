config = AlphaConfig()
def alpha_employment_pressure(s:Streams):
    """
    Hypothesis:  A positive value, indicating a decrease in the short-term unemployment rate (2 months)
    relative to the medium-term rate (6 months), suggests an economic recovery with rising production levels,
    potentially boosting demand for base metals and increasing their prices.
    """
    tur = ts_ffill(s.lme_us_unemp_rate)
    tur_2mma = ts_mean(tur, window=month_2)
    tur_3mma = ts_mean(tur, window=quarterly)
    return tur_2mma - tur_3mma
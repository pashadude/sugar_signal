config = AlphaConfig()
def unemp_cur_in_circ_corr(s:Streams):
    """
    Hypothesis: The correlation between U.S. unemployment rate changes and currency in circulation reflects economic stress.
    A negative correlation suggests rising unemployment with increased liquidity, potentially weakening base metal prices.
    """
    unemp_rate = ts_ffill(s.lme_us_unemp_rate)
    cur_in_circ = ts_ffill(s.lme_us_cur_in_circ)
    unemp_rate_diff_ma = ts_mean(delta(unemp_rate, period=month), window=month_2)
    cur_in_circ_diff_ma = ts_mean(delta(cur_in_circ, period=week), window=month)
    unemp_rate_cur_in_circ_corr =  correlation(unemp_rate_diff_ma, cur_in_circ_diff_ma, window=month)
    return - unemp_rate_cur_in_circ_corr
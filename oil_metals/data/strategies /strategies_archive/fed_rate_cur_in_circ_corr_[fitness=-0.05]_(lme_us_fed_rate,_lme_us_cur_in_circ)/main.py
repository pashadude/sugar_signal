config = AlphaConfig()
def fed_rate_cur_in_circ_corr(s:Streams):
    """
    Hypothesis: The correlation between the monthly percentage changes in the U.S. Federal Funds Rate
    and Currency in Circulation reflects monetary policy dynamics.
    A stronger positive correlation may indicate synchronized tightening or loosening,
    influencing base metal prices through liquidity and credit conditions.
    """
    fed_rate = ts_ffill(s.lme_us_fed_rate)
    cur_in_circ = ts_ffill(s.lme_us_cur_in_circ)
    fed_rate_pct = ts_pct_change(fed_rate, periods=month)
    cur_in_circ_pct = ts_pct_change(cur_in_circ, periods=month)
    fed_rate_pct_zn = zscore(fed_rate_pct, window=week_2)
    cur_in_circ_pct_zn = zscore(cur_in_circ_pct, window=week_2)
    fed_rate_cur_in_circ_corr =  correlation(fed_rate_pct_zn, cur_in_circ_pct_zn, window=week_2)
    return fed_rate_cur_in_circ_corr
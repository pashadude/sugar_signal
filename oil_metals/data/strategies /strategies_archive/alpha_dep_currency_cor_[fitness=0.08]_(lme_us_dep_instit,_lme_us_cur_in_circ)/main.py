config = AlphaConfig()
def alpha_dep_currency_cor(s: Streams):
    """
    Hypothesis: A positive correlation between average 3-weeks values of deposits held by banks
    and non-banking institutions at the Federal Reserve and the currency circulated in the economy
    indicates economic stimulation through currency emission, which is then channeled back into the real economy by financing enterprises.
    """
    dep_instit = ts_ffill(s.lme_us_dep_instit)
    cur_in_circ = ts_ffill(s.lme_us_cur_in_circ)
    dep_instit_ma15 = ts_mean(dep_instit, window=week_3)
    cur_in_circ_ma15 = ts_mean(cur_in_circ, window=week_3)
    return correlation(dep_instit_ma15, cur_in_circ_ma15, window=week_3)
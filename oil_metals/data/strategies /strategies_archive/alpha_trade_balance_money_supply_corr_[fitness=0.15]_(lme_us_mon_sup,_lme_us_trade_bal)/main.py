config = AlphaConfig()
def alpha_trade_balance_money_supply_corr(s:Streams):
    """
    Hypothesis: Increase in divergence between the U.S. Trade Balance and Money Supply (M2)
    indicates stronger economic conditions, resulting in higher demand for base metals and a rise in their prices.
    """
    trade_bal = ts_ffill(s.lme_us_trade_bal)
    m2 = ts_ffill(s.lme_us_mon_sup)
    trade_bal_3mma = ts_mean(trade_bal, window=quarterly)
    m2_3mma = ts_mean(m2, window=quarterly)
    trade_bal_m2_corr = correlation(trade_bal_3mma, m2_3mma)
    return - trade_bal_m2_corr
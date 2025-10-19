config = AlphaConfig()
def alpha_trade_to_money_ratio(s:Streams):
    """
    Hypothesis: The Trade-to-Money Ratio compares the U.S. trade balance to money supply (M2).
    A lower ratio indicates looser monetary conditions [weaker U.S. dollar], likely boosting demand and base metal prices.
    A higher ratio suggests tighter conditions [strong U.S. dollar], potentially weakening base metal prices.
    """
    trade_bal = ts_ffill(s.lme_us_trade_bal)
    m2 = ts_ffill(s.lme_us_mon_sup)
    trade_to_money_ratio = safe_div(trade_bal, m2)
    return - trade_to_money_ratio
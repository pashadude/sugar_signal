config = AlphaConfig()
def alpha_tres_bal_zn(s: Streams):
    """
    Hypothesis: Decreasing normalized percent change of the Treasury balance indicates Federal Reserve actions
    to stimulate the economy through lower bond interest rates, leading to reduced overall interest rates,
    increased economic activity, and higher demand and prices for base metals. Conversely,
    an increase in the Treasury balance may signal restrictive policies, resulting in reduced demand and lower base metal prices.
    """
    tres_bal = ts_ffill(s.lme_us_tres_bal)
    tres_bal_per = delta(tres_bal, period=week_2)
    tres_bal_sma_sma84 = ts_mean(tres_bal_per, window=month)
    return - zscore(tres_bal_sma_sma84, window=month)
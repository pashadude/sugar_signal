config = AlphaConfig()
def alpha_tres_bal_delta(s: Streams):
    """
    Hypothesis: In times of market risk, the Federal Reserve may increase its balance sheet by issuing new bonds
    and withdrawing liquidity, which can shrink the economy and lead to a decrease in base metal prices.
    """
    tres_bal = ts_ffill(s.lme_us_tres_bal)
    return - delta(tres_bal, period=month)
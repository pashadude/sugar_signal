config = AlphaConfig()
def alpha_tres_close_price_cor(s: Streams):
    """
    Hypothesis: Positive correlation between the FED Treasury balance and closing prices may indicate rising bond yields,
    a stronger dollar, and a later increase in base metal prices.
    """
    tres_bal = ts_ffill(s.lme_us_tres_bal)
    tres_bal_ma15 = ts_mean(tres_bal, window=week_3)
    close = s.lme_close_price
    close_ma15 = ts_mean(close, window=week_3)
    return correlation(tres_bal_ma15, close_ma15, window=week_3)
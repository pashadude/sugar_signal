config = AlphaConfig()
def alpha_tres_bal_fed_assets_ratio(s: Streams):
    """
    Hypothesis: Positive ratio from average values of treasury issuance and treasuries held in the FED account
    indicates rates of increasing the liquidity of the banking system to stimulate commodity demand and prices.
    """
    tres_bal = s.lme_us_tres_bal.ffill()
    fed_assets = s.lme_us_fed_assets.ffill()
    tres_bal_ma15 = ts_mean(tres_bal, window=week_3)
    fed_assets_ma15 = ts_mean(fed_assets, window=week_3)
    return safe_div(tres_bal_ma15, fed_assets_ma15)
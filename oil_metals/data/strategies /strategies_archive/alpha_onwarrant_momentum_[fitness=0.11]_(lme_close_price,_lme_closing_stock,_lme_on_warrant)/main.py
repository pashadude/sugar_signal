config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_onwarrant_momentum(s: Streams, window=7):
    """Hypothesis: Computes an alpha factor based on the momentum of the on-warrant ratio."""
    price_mom = s.lme_close_price - ts_mean(s.lme_close_price, window=window)
    total_stock = s.lme_closing_stock
    on_warrant_ratio = safe_div(s.lme_on_warrant, total_stock)
    return price_mom * (delta(on_warrant_ratio, period=window))
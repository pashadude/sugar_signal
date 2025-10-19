config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_relative_stock_tightening(s: Streams, window=5):
    """Hypoesis: Computes an alpha factor based on the relative stock tightening."""

    rel_stock = s.lme_on_warrant - s.lme_cancelled_stock
    price_range = (s.lme_high_price - s.lme_low_price) / s.lme_close_price
    return -price_range * (-delta(rel_stock, period=window))
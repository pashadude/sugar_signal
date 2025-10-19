config = AlphaConfig(booksize = 10000000.0, neutralization = 'market')
def alpha_inventory_price_corr(s: Streams, window=7):
    """Hypothesis: Computes an alpha factor based on the correlation between inventory and price changes."""
    price_change = delta(s.lme_close_price, period=window)
    stock_change = delta(s.lme_closing_stock, period=window)
    corr = correlation(price_change, stock_change, window=window)
    return corr
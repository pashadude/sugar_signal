config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_inventory_depletion(s: Streams, window=5):
    # Negative delta in closing stock (depletion) is bullish, so we invert sign
    return delta(s.lme_closing_stock, period=window)
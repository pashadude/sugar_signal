config = AlphaConfig(start_date = '2013-01-01', neutralization = 'market')
def alpha_price_value(
        s: Streams,
) -> pd.DataFrame:
    """
    Hypothesis: Based on a trading strategy on value,
    which in this case is ratio of price 5 years ago to recent price.

    This alpha should be considered long-form strategy.
    """

    data = s.lme_close_price
    value = safe_div(ts_delay(data, 255 * 5), data)

    return rank(value)
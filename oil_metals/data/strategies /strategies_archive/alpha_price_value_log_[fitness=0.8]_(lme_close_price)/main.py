config = AlphaConfig(neutralization = 'market')
def alpha_price_value_log(
        s: Streams,
) -> pd.DataFrame:
    """
    Hypothesis: Based on a trading strategy on value, modified to use the log values of price
    and ratio of the 2 years ago price to the recent one.
    """

    data = ts_log10(s.lme_close_price)
    past_returns = ts_delay(data, 255 * 2)
    value = safe_div(past_returns, data)

    return rank(value)
config = AlphaConfig(neutralization = 'market')
def alpha_closing_to_cancelled(
        s: Streams
):
    """
    Hypothesis: basic supply and demand - the bigger ratio of overall to cancelled stock ->
    more stock available -> more supply -> price might go down.
    And vice versa. In addition, if None or 0 stocks are cancelled,
    we're supposing that there is demand and not enough supply, so we give those events bigger weight.
    """
    res = -safe_div(s.lme_closing_stock, s.lme_cancelled_stock)
    res[res < -25] = -25
    res[res == 0] = 25

    return res
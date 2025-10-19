config = AlphaConfig(start_date = '2009-01-01')
def alpha_us_pmi(
        s: Streams,
) -> pd.DataFrame:
    """
    Hypothesis: changes of the US Purchasing Managers' Index could reflect
    the price in the short term and in long term. Combine that in the sum of different periods.
    """

    us_pmi = ts_ffill(s.lme_us_pmi)
    result = us_pmi.copy()
    result[:] = 0

    for period in [5, 22, 65, 252]:
        result = result + ts_pct_change(us_pmi, period).fillna(0)

    return result
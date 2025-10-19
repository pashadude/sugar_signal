config = AlphaConfig()
def alpha_mxn_jpy_change(
        s: Streams,
        window=20
) -> pd.DataFrame:
    """
    Hypothesis: MX is the large exporter, JP is the large importer. This alpha keeps the ratio between currencies
    and reacts as a signal if it changes from the past month.
    """

    return ts_pct_change(safe_div(s.lme_fx_mxn, s.lme_fx_jpy), window)
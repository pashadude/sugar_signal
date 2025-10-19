config = AlphaConfig()
def alpha_aud_mxn_corr(
        s: Streams,
        window=10
) -> pd.DataFrame:
    """
    Hypothesis: AU and MX are large exporters of metals. If their currencies are highly correlated,
    it might affect the world commodity prices
    """

    return -correlation(s.lme_fx_aud, s.lme_fx_mxn, window)
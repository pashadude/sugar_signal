config = AlphaConfig()
def alpha_mxn_aud_divergence_corr(
        s: Streams,
        window=60,
        corr_window=20
) -> pd.DataFrame:
    """
    Hypothesis: MXN and AUD are large exporters. Strong correlation between divergence of the currency
    from its quarterly mean in both countries might cause the metal prices to go down
    """
    aud = s.lme_fx_aud - ts_mean(s.lme_fx_aud, window)
    mxn = s.lme_fx_mxn - ts_mean(s.lme_fx_mxn, window)

    return -correlation(aud, mxn, corr_window)
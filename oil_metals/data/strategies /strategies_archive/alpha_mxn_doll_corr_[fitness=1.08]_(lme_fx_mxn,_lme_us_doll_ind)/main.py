config = AlphaConfig()
def alpha_mxn_doll_corr(
        s: Streams,
        window=10
) -> pd.DataFrame:
    """
    Hypothesis: MX is the large exporter and its economy closely tied to the USA. Strong correlation between
    MXN currency and dollar might indicate stable growth in export economy.
    """

    return correlation(s.lme_fx_mxn, s.lme_us_doll_ind, window)
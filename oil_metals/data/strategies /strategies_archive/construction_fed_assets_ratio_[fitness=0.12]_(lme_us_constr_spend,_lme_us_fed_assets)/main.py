config = AlphaConfig()
def construction_fed_assets_ratio(s:Streams):
    """
    Hypothesis: The Construction-to-Federal Assets Ratio compares U.S. construction spending growth to Federal Reserve asset growth.
    A higher ratio suggests rising construction activity relative to monetary expansion, potentially signaling stronger economic demand and higher base metal prices,
    while a lower ratio may indicate weaker demand conditions.
    """
    construction_fed_assets_ratio = safe_div(
        zscore(ts_mean(ts_pct_change(ts_ffill(s.lme_us_constr_spend), periods=month), window=month_2), window=month),
        zscore(ts_mean(ts_pct_change(ts_ffill(s.lme_us_fed_assets), periods=week), window=week_2), window=week)
    )
    return construction_fed_assets_ratio
config = AlphaConfig()
def alpha_fed_assets_momentum(s: Streams):
    """
    Hypothesis: A positive percent change in total Federal Assets suggests a higher likelihood of the Federal Reserve
    interventions to stimulate the economy through quantitative easing (QE), increasing demand for base metals.
    Conversely, negative values indicate the opposite effect.
    """
    fed_assets = ts_ffill(s.lme_us_fed_assets)
    fed_assets_per = ts_pct_change(fed_assets, periods=month)
    fed_assets_ma21 = ts_mean(fed_assets_per, window=month)
    fed_assets_ma30 = ts_delay(fed_assets_ma21, period=week_2)
    return fed_assets_ma30 - fed_assets_ma21
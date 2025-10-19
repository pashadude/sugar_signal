config = AlphaConfig()
def alpha_eur_on_warrant_div(
        s: Streams,
        window=5
) -> pd.DataFrame:
    """
    Hypothesis: The relative change in the EUR exchange rate compared to the on-warrant stock level
    reflects shifts in supply and demand dynamics in Euro zone
    """
    return ts_pct_change(safe_div(s.lme_fx_eur, s.lme_on_warrant), window)
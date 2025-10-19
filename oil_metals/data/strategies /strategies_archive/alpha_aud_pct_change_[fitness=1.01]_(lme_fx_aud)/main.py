config = AlphaConfig()
def alpha_aud_pct_change(
        s: Streams,
        change_window=20,
        delay_window=5
) -> pd.DataFrame:
    """
    Hypothesis: A delayed negative percentage change in the AUD exchange rate
    might signal the increase in metal prices (long positions)
    """
    res = -ts_delay(ts_pct_change(s.lme_fx_aud, change_window), delay_window)
    res = ts_where(res, res > 0, 0)

    return res
config = AlphaConfig()
def alpha_us_china_rsi(
    s: Streams,
    lookback: int = 63
) -> pd.DataFrame:
    """
    Thesis:
    The RSI gap (US yield diff minus Hang Seng momentum) can early-flag a bullish environment
    for base metals prices where US-driven financial forces are propping up commodity prices before
    China’s physical demand joins the party. Although China dominates in raw commodity consumption, 
    the US  exerts a disproportionately large influence on price formation through financial channels.
        
    """
    # Step 1: Forward-fill data
    us_yield_diff   = ts_ffill(s.lme_us_10_2_rate) # The difference between long-term and short-term Treasury yields. It is used as an indicator of economic outlook and potential recession risks.
    hang_seng_index = ts_ffill(s.lme_hang_seng_ind )      # Tracks China's coal industry performance


    # Step 2: Compute RSI
    rsi_us_yield_diff   = ts_rsi(us_yield_diff, period=lookback)
    rsi_hang_seng_index = ts_rsi(hang_seng_index, period=lookback)

    # Step 3: Difference in RSI
    signal = rsi_us_yield_diff - rsi_hang_seng_index

    signal = ts_mean(signal,lookback)
    return signal
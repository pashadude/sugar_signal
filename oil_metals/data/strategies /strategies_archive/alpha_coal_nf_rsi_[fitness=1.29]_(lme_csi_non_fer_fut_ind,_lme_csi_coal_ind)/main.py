config = AlphaConfig()
def alpha_coal_nf_rsi(
    s: Streams,
    lookback: int = 63
) -> pd.DataFrame:
    """
    Thesis:
        The difference between the Non-Ferrous Metals RSI and the Coal RSI reflects
        idiosyncratic demand or supply factors in base metals relative
        to broader energy markets in China.
        
    """
    # Step 1: Forward-fill data
    csi_nf_index   = ts_ffill(s.lme_csi_non_fer_fut_ind) # Tracks futures prices for non-ferrous metals
    csi_coal_index = ts_ffill(s.lme_csi_coal_ind)      # Tracks China's coal industry performance


    # Step 2: Compute RSI
    rsi_csi_nf_index   = ts_rsi(csi_nf_index, period=lookback)
    rsi_csi_coal_index = ts_rsi(csi_coal_index, period=lookback)

    # Step 3: Difference in RSI
    signal = rsi_csi_nf_index - rsi_csi_coal_index

    return signal
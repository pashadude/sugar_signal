config = AlphaConfig()
def alpha_vix_regime_filter(s: Streams, ma_window=63) -> pd.DataFrame:
    """
    Hypothesis:
    1) A declining VIX (negative 5-day delta) indicates a calmer, 'risk-on' environment, 
       so we take a positive signal proportional to 1 / VIX_delta.
    2) If the absolute VIX level exceeds a threshold (mean + 1 * std), we interpret it 
       as a high-volatility regime and shut off the signal entirely.

    Explanation:
    - Equity markets (tracked by VIX) often react faster to macro shocks than base metals. 
      By using a 5-day delay, we assume risk assets have already priced in the macro event, 
      and base metals are next to follow. Thus, we align with the idea that base metals 
      will 'catch up' to the equity volatility signal with a short lag.
    - We also smooth the 5-day delta over a 63-day window to reduce daily noise 
      and apply a log transform to mitigate extreme spikes in the final signal.
    """
    # Step 1: Forward-fill raw VIX data & convert to daily decimal
    vix_raw = ts_ffill(s.lme_us_vix)
    vix_decimal_daily = (vix_raw / 100) / np.sqrt(252)
    
    # Step 2: Compute 5-day delta and then smooth it
    vix_delta = delta(vix_decimal_daily, 5)
    vix_delta_smoothed = ts_mean(vix_delta, ma_window)
    
    # Step 3: Determine high-vol regime based on threshold
    vix_mean = vix_raw.mean()
    vix_std  = vix_raw.std()
    threshold = vix_mean + 1 * vix_std
    high_vol_mask = vix_raw > threshold
    downweight_factor = np.where(high_vol_mask, 0, 1.0)
    
    # Step 4: Risk-on signal = 1 / smoothed VIX delta, delayed by 5 days
    raw_signal = 1 / vix_delta_smoothed
    signal_delayed = ts_delay(raw_signal, 5)
    
    # Step 5: Apply downweight factor and return log-transformed signal
    final_signal = signal_delayed * downweight_factor
    return np.log(final_signal)
config = AlphaConfig()
def alpha_china_export_inflation(s: Streams, window=252, smoothing_window=21) -> pd.DataFrame:
    """
    Thesis:
    When China's CPI growth outpaces that of the US, China effectively "exports" inflation to the 
    global market. This stronger Chinese economy supports higher demand for base metals, driving
    prices higher. Conversely, if US CPI growth surpasses China's, it may signal weaker Chinese demand,
    dampening base metal prices.
    """

 
    # Step 1: Retrieve and Forward-Fill CPI Data
    cn_cpi = ts_ffill(s.lme_cn_cpi)  # China CPI
    us_cpi = ts_ffill(s.lme_us_cpi)  # US CPI

    # Step 2: Calculate Year-over-Year (YoY) CPI Growth
    cn_cpi_yy = ts_pct_change(cn_cpi, window) * 100  # China CPI % change over 1 year
    us_cpi_yy = ts_pct_change(us_cpi, window) * 100  # US CPI % change over 1 year


    # Step 3: Compute the Ratio and Invert the Signal
    ratio = safe_div(us_cpi_yy, cn_cpi_yy)

    # Invert the ratio:
    # Positive → China leads, Negative → US leads
    inverted_signal = -ratio

    # ---------------------------
    # Step 4: Smooth the Signal
    # ---------------------------
    # Apply a rolling mean to reduce short-term noise
    smoothed_signal = ts_mean(inverted_signal, window=smoothing_window)

   
    # Return the Final Signal
    return smoothed_signal
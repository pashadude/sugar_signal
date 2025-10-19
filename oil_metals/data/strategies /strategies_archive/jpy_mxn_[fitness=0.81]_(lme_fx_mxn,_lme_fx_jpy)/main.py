config = AlphaConfig()
def jpy_mxn(s: Streams, corr_window=10, smooth_window=1):

    # 1) Compute rolling correlation
    corr_raw = correlation(s.lme_fx_jpy, s.lme_fx_mxn, corr_window)

    # 2) Smooth the correlation
    corr_smooth = ts_mean(corr_raw, window=smooth_window)

    return corr_smooth
config = AlphaConfig()
def alpha_stock_in_out_and_volume(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    Big wave of stock in/out vs full/low stock.

    - Short: lme_stock_in > 27-day SMA of lme_stock_in AND lme_volume >= 15-day avg of lme_volume.
    - Long: lme_stock_out < 27-day SMA of lme_stock_out AND lme_volume <= 15-day avg of lme_volume.
    """
    res = ((((s.lme_stock_in > ts_mean(s.lme_stock_in, window=27)) &
             (s.lme_volume >= ts_mean(s.lme_volume, window=15))) * -1) +
           ((s.lme_stock_out < ts_mean(s.lme_stock_out, window=27)) &
            (s.lme_volume <= ts_mean(s.lme_volume, window=15))) * 1) * s.lme_volume

    return res
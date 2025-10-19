config = AlphaConfig()
def alpha_dual_sma_close_price(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    Fake trend reversal within bigger trend(part 2)
    
    - Long: 1st SMA (34 days) ≥ 2nd SMA (44 days) AND Closing Price ≥ 1st SMA OR 2nd SMA
    - Short: 2nd SMA (44 days) ≥ 1st SMA (34 days) AND Closing Price < 1st SMA OR 2nd SMA
    """
    return ((
        (
            (ts_mean(s.lme_close_price, window=34) >= ts_mean(s.lme_close_price, window=44)) &
            (
                (s.lme_close_price >= ts_mean(s.lme_close_price, window=34)) |
                (s.lme_close_price >= ts_mean(s.lme_close_price, window=44))
            )
        ) * 1
    ) + (
        (
            (ts_mean(s.lme_close_price, window=44) >= ts_mean(s.lme_close_price, window=34)) &
            (
                (s.lme_close_price < ts_mean(s.lme_close_price, window=34)) |
                (s.lme_close_price < ts_mean(s.lme_close_price, window=44))
            )
        ) * -1
    )) *s.lme_volume
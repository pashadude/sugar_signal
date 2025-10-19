config = AlphaConfig()
def alpha_crossover_macd(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    - Long: MACD Line (20-day SMA - 18-day SMA) crosses above Signal Line (3-day SMA of MACD Line).
    - Short: MACD Line (20-day SMA - 18-day SMA) crosses below Signal Line (3-day SMA of MACD Line).
    """
    return (
        (
            (ts_mean(s.lme_close_price, window=20) - ts_mean(s.lme_close_price, window=18)) >
            ts_mean(
                (ts_mean(s.lme_close_price, window=20) - ts_mean(s.lme_close_price, window=18)),
                window=3
            )
        ) * s.lme_volume
    ) + (
        (
            (ts_mean(s.lme_close_price, window=20) - ts_mean(s.lme_close_price, window=18)) <
            ts_mean(
                (ts_mean(s.lme_close_price, window=20) - ts_mean(s.lme_close_price, window=18)),
                window=3
            )
        ) * -s.lme_volume
    )
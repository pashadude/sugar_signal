config = AlphaConfig()
def alpha_dsma_and_stocks(s: Streams) -> pd.DataFrame:
    """
    Hypothesis:
    Fake trend reversal within bigger trend + Big wave of stock in/out
    
    - Short: Closing price positioned between 3-day and 10-day SMAs, AND lme_stock_in > 20-day SMA of lme_stock_out.
    - Long: Closing price positioned between 3-day and 10-day SMAs, AND lme_stock_out < 20-day SMA of lme_stock_in.
    """
    return (
            (((s.lme_close_price >= ts_mean(s.lme_close_price, window=3)) &
            (s.lme_close_price <= ts_mean(s.lme_close_price, window=10)) &
            (s.lme_stock_in > ts_mean(s.lme_stock_out, window=20))) * -1) +
            ((s.lme_close_price <= ts_mean(s.lme_close_price, window=3)) &
            (s.lme_close_price >= ts_mean(s.lme_close_price, window=10)) &
            (s.lme_stock_out < ts_mean(s.lme_stock_in, window=20))) * 1) * s.lme_volume
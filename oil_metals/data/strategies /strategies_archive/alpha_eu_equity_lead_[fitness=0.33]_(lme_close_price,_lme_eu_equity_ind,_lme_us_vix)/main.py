config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def alpha_eu_equity_lead(s: Streams, window=5):
    eu_mom = s.lme_eu_equity_ind - ts_mean(s.lme_eu_equity_ind, window=window)
    vix_change = delta(s.lme_us_vix, period=window)
    price_lag = s.lme_close_price - ts_mean(s.lme_close_price, window=window)
    result = eu_mom * (1 - vix_change) * (-price_lag)

    return -result
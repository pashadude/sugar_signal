config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def oi_acceleration(s: Streams, window=1):
    """Second derivative of Open Interest."""
    oi_velocity = s.lme_open_interest.diff(window)
    oi_acceleration = oi_velocity.diff(window)
    result = oi_acceleration
    return -result
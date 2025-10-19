config = AlphaConfig(booksize = 10000000.0, start_date = '2021-10-20', neutralization = 'market')
def normalised_signal(s: Streams):
    """Normalised signal."""
    result = (
        s.lme_open_interest - s.lme_open_interest.mean()
    ) / s.lme_open_interest.std() + (
        s.lme_volume - s.lme_volume.mean()
    ) / s.lme_volume.std()

    return -result
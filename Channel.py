import math


WAVELENGTH = 785e-9            # m
TRANSMITTER_APERTURE = 0.50    # m
RECEIVER_APERTURE = 0.30       # m

FRIED_PARAMETER = 0.075        # m
ATM_VERTICAL_LOSS_DB = 1.0     # dB
POINTING_EFFICIENCY = 0.80
OPTICS_LOSS_DB = 3.0           # dB

MIN_ELEVATION_DEG = 10.0


def optical_channel(elevation_deg, range_km):

    if elevation_deg < MIN_ELEVATION_DEG:
        return 0.0

    range_m = range_km * 1000.0

    # Diffraction + turbulence
    theta_diffraction = WAVELENGTH / TRANSMITTER_APERTURE
    theta_turbulence = WAVELENGTH / FRIED_PARAMETER

    theta_total_sq = (
        theta_diffraction**2
        + theta_turbulence**2
    )

    geometric_probability = (
        RECEIVER_APERTURE**2
        / (range_m**2 * theta_total_sq)
    )

    geometric_probability = min(1.0, geometric_probability)

    # Atmospheric survival probability
    elevation_rad = math.radians(elevation_deg)

    atmospheric_loss_db = (
        ATM_VERTICAL_LOSS_DB
        / math.sin(elevation_rad)
    )

    atmospheric_probability = (
        10 ** (-atmospheric_loss_db / 10.0)
    )

    # Fixed optical losses
    pointing_probability = POINTING_EFFICIENCY

    optics_probability = (
        10 ** (-OPTICS_LOSS_DB / 10.0)
    )

    # Total probability that the photon survives the channel
    survival_probability = (
        geometric_probability
        * atmospheric_probability
        * pointing_probability
        * optics_probability
    )

    return max(0.0, min(1.0, survival_probability))
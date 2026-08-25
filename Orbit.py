from skyfield.api import load, wgs84
from datetime import timedelta


def load_iss_tle():
    # ISS TLE
    ts = load.timescale()

    # Get current TLE
    stations_url = (
        "https://celestrak.org/NORAD/elements/gp.php"
        "?GROUP=stations&FORMAT=tle"
    )

    satellites = load.tle_file(stations_url, reload=True)
    by_name = {sat.name: sat for sat in satellites}

    satellite = by_name["ISS (ZARYA)"]
    return satellite, ts    

def find_next_pass():
    satellite, ts = load_iss_tle()
    # McMaster
    observer = wgs84.latlon(
        43.2640,
        -79.9181
    )

    # Search far enough ahead to find a pass
    t0 = ts.now()
    t1 = ts.from_datetime(
        t0.utc_datetime() + timedelta(days=7)
    )

    times, events = satellite.find_events(
        observer,
        t0,
        t1,
        altitude_degrees=10
    )

    # Find first complete rise -> set
    pass_start = None
    pass_end = None

    for t, event in zip(times, events):

        if event == 0 and pass_start is None:
            pass_start = t

        elif event == 2 and pass_start is not None:
            pass_end = t
            break

    if pass_start is None or pass_end is None:
        raise RuntimeError("No complete pass found")

    # Generate pass data every second
    start = pass_start.utc_datetime()
    end = pass_end.utc_datetime()

    duration = int((end - start).total_seconds())

    pass_data = []

    for second in range(duration + 1):

        current_time = start + timedelta(seconds=second)
        t = ts.from_datetime(current_time)

        topocentric = (satellite - observer).at(t)
        elevation, azimuth, distance = topocentric.altaz()

        pass_data.append({
            "time": current_time,
            "seconds": second,
            "elevation_deg": elevation.degrees,
            "azimuth_deg": azimuth.degrees,
            "range_km": distance.km,
        })
    return {
        "start": start,
        "end": end,
        "duration": duration,
        "data": pass_data
}
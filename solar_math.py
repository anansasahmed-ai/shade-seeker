import pandas as pd
from pvlib import solarposition


def get_sun_position(lat, lon, dt_utc):
  """Calculates the solar azimuth and elevation for a given latitude, longitude,

  and datetime (UTC).
  """
  times = pd.DatetimeIndex([dt_utc])
  solpos = solarposition.get_solarposition(times, lat, lon)
  return {
      "azimuth": float(solpos["azimuth"].iloc[0]),
      "elevation": float(solpos["elevation"].iloc[0]),
  }

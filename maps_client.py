import math
import polyline
import requests


class MapsClient:

  def __init__(self, api_key):
    if not api_key:
      raise ValueError("Google Maps API Key is missing.")
    self.api_key = api_key
    self.routes_url = (
        "https://routes.googleapis.com/directions/v2:computeRoutes"
    )

  def get_route_data(
      self, origin_str, destination_str, travel_mode="DRIVE", departure_time=None
  ):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": self.api_key,
        "X-Goog-FieldMask": (
            "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
        ),
    }

    payload = {
        "origin": {"address": origin_str},
        "destination": {"address": destination_str},
        "travelMode": travel_mode,
    }

    if departure_time:
      payload["departureTime"] = departure_time.isoformat()
      if travel_mode == "DRIVE":
        payload["routingPreference"] = "TRAFFIC_AWARE"

    response = requests.post(self.routes_url, headers=headers, json=payload)
    data = response.json()

    if "error" in data:
      raise ValueError(f"Google Routes API Error: {data['error']['message']}")

    if "routes" not in data or len(data["routes"]) == 0:
      raise ValueError(
          "No routes found between these locations. Check your addresses."
      )

    route = data["routes"][0]
    encoded_polyline = route["polyline"]["encodedPolyline"]

    duration_str = route["duration"].replace("s", "")
    total_duration_seconds = float(duration_str)
    coordinates = polyline.decode(encoded_polyline)

    return coordinates, total_duration_seconds


def calculate_bearing(lat1, lon1, lat2, lon2):
  lat1_rad = math.radians(lat1)
  lat2_rad = math.radians(lat2)
  dlon_rad = math.radians(lon2 - lon1)

  x = math.sin(dlon_rad) * math.cos(lat2_rad)
  y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(
      lat1_rad
  ) * math.cos(lat2_rad) * math.cos(dlon_rad)

  bearing_rad = math.atan2(x, y)
  bearing_deg = math.degrees(bearing_rad)
  return (bearing_deg + 360) % 360

import datetime
import math
from maps_client import MapsClient, calculate_bearing
from solar_math import get_sun_position
import streamlit as st

st.set_page_config(page_title="Shade Seeker", page_icon="☀️", layout="centered")

st.title("☀️ Shade Seeker")
st.write(
    "Determine optimal seating (Left vs. Right) to minimize direct sun exposure"
    " on transit routes."
)
# --- APP PASSWORD PROTECTION ---
# Change "my_secret_pin" to whatever password you want to use
APP_PASSWORD = "8749"

password_input = st.text_input("🔒 Enter App Password to Unlock", type="password")
if password_input != APP_PASSWORD:
  st.warning(
      "Please enter the correct password to access Shade Seeker."
  )
  st.stop()
# Securely load API Key from Streamlit Secrets (with sidebar fallback for local testing)
api_key = ""
try:
  api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
except Exception:
  api_key = st.sidebar.text_input("Google Maps API Key", type="password")

with st.form("shade_form"):
  origin = st.text_input("Start Location", "Denali Park Visitor Center, AK")
  destination = st.text_input("Destination", "Anchorage, AK")

  travel_mode_choice = st.selectbox(
      "Travel Mode", ["Driving / Road (Car, Bus)", "Train / Public Transit"]
  )
  travel_mode = "TRANSIT" if "Train" in travel_mode_choice else "DRIVE"

  use_custom_time = st.checkbox("Specify custom departure time?")
  departure_time_utc = None
  if use_custom_time:
    col1, col2 = st.columns(2)
    d = col1.date_input("Date", datetime.date.today())
    t = col2.time_input("Time", datetime.datetime.now().time())
    local_dt = datetime.datetime.combine(d, t)
    departure_time_utc = local_dt.replace(tzinfo=datetime.timezone.utc)
  else:
    # Buffer 2 minutes ahead to satisfy Google's future timestamp requirement
    departure_time_utc = datetime.datetime.now(
        datetime.timezone.utc
    ) + datetime.timedelta(minutes=2)

  submitted = st.form_submit_button("Calculate Best Side")

if submitted:
  if not api_key:
    st.error("Please configure your Google Maps API Key.")
  else:
    with st.spinner("Analyzing route geometry and sun angles..."):
      try:
        client = MapsClient(api_key=api_key)
        coords, total_duration_seconds = client.get_route_data(
            origin,
            destination,
            travel_mode=travel_mode,
            departure_time=departure_time_utc,
        )

        if not coords or len(coords) < 2:
          st.error("Route data returned insufficient points for analysis.")
        else:
          num_checkpoints = 20
          step = max(1, len(coords) // num_checkpoints)
          sampled_coords = coords[::step]

          left_score = 0
          right_score = 0
          sun_up_count = 0
          time_per_segment = total_duration_seconds / max(
              1, len(sampled_coords) - 1
          )

          for i in range(len(sampled_coords) - 1):
            lat1, lon1 = sampled_coords[i]
            lat2, lon2 = sampled_coords[i + 1]
            heading = calculate_bearing(lat1, lon1, lat2, lon2)

            elapsed = i * time_per_segment
            cur_time = departure_time_utc + datetime.timedelta(
                seconds=elapsed
            )

            sun = get_sun_position(lat1, lon1, cur_time)
            elevation = sun["elevation"]

            if elevation <= 0:
              continue

            sun_up_count += 1
            sun_az = sun["azimuth"]

            rel_angle = (sun_az - heading + 360) % 360
            if rel_angle > 180:
              rel_angle -= 360

            intensity_weight = max(
                0.1, math.sin(math.radians(elevation))
            ) * abs(math.sin(math.radians(rel_angle)))

            if rel_angle > 0:
              right_score += intensity_weight
            else:
              left_score += intensity_weight

          st.divider()
          st.subheader("Analysis Results")

          if sun_up_count == 0:
            st.info(
                "🌙 The entire trip takes place after dark. Seating side doesn't"
                " matter."
            )
          else:
            total = left_score + right_score
            if total == 0:
              st.info(
                  "☁️ Sun elevation is very high overhead. Minimal"
                  " side-window exposure expected."
              )
            else:
              l_pct = (left_score / total) * 100
              r_pct = (right_score / total) * 100

              m_col1, m_col2 = st.columns(2)
              m_col1.metric("Left Side Exposure", f"{l_pct:.1f}%")
              m_col2.metric("Right Side Exposure", f"{r_pct:.1f}%")

              if left_score < right_score:
                st.success(
                    "🏆 **RECOMMENDATION: Sit on the LEFT side of the vehicle"
                    " for minimal sun exposure.**"
                )
              else:
                st.success(
                    "🏆 **RECOMMENDATION: Sit on the RIGHT side of the vehicle"
                    " for minimal sun exposure.**"
                )

      except Exception as e:
        st.error(f"Error: {e}")

import time
import requests
from datetime import datetime, timezone
import json

# retrieve solar flare data
def get_solar_flare_data():
    try:
        url = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-minute.json"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        if not data:
            return None

        latest = data[-1]

        time_str = latest.get("time_tag")
        flux = latest.get("flux")
        energy_range = latest.get("energy_range")

        if time_str is None or flux is None or energy_range is None:
            return None

        if "0.1-0.8" not in energy_range:
            return None

        ts = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

        flux = float(flux)

        return {
            "timestamp": ts,
            "flux": flux,
            "energy_range": energy_range
        }

    except Exception:
        return None

# classify solar flare
def classify_flare(flux):
    if flux >= 1e-4:
        base = "X"
        level = flux / 1e-4
    elif flux >= 1e-5:
        base = "M"
        level = flux / 1e-5
    elif flux >= 1e-6:
        base = "C"
        level = flux / 1e-6
    elif flux >= 1e-7:
        base = "B"
        level = flux / 1e-7
    elif flux >= 1e-8:
        base = "A"
        level = flux / 1e-8
    else:
        return "Below A"

    return f"{base}{level:.1f}"

# anomaly detector for solar flare
def detect_solar_flare_spike(data):
    return data and data["flux"] >= 1e-8

# retrieve solar wind data
def get_solar_wind_data():
    try:
        plasma_url = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-minute.json"
        mag_url = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-minute.json"

        plasma_res = requests.get(plasma_url)
        plasma_res.raise_for_status()
        plasma_data = plasma_res.json()

        mag_res = requests.get(mag_url)
        mag_res.raise_for_status()
        mag_data = mag_res.json()

        if len(plasma_data) < 2 or len(mag_data) < 2:
            return None

        plasma_last = plasma_data[-1]
        mag_last = mag_data[-1]

        p_time_str = plasma_last[0]
        density = float(plasma_last[1])
        speed = float(plasma_last[2])
        temperature = float(plasma_last[3])

        m_time_str = mag_last[0]
        bz = float(mag_last[3])
        bt = float(mag_last[4])

        ts = datetime.fromisoformat(p_time_str.replace("Z", "+00:00"))

        return {
            "timestamp": ts,
            "density": density,
            "speed": speed,
            "temperature": temperature,
            "bz": bz,
            "bt": bt
        }
    except Exception:
        return None

# retain simple previous sample in memory for shock detection
_prev_wind_sample = None

# anomaly detector for solar wind shock
def detect_solar_wind_shock(data):
    global _prev_wind_sample

    if data is None:
        return False

    if _prev_wind_sample is None:
        _prev_wind_sample = data
        return False

    prev = _prev_wind_sample
    curr = data

    speed_jump = abs(curr["speed"] - prev["speed"])
    density_jump = abs(curr["density"] - prev["density"])
    temp_jump = abs(curr["temperature"] - prev["temperature"])
    bz = curr["bz"]

    shock = (
        speed_jump >= 50 or
        density_jump >= 5 or
        temp_jump >= 20000 or
        bz <= -5
    )

    _prev_wind_sample = curr
    return shock

# event correlation logic
def correlate_events(events):
    active = [k for k, v in events.items() if v is not None]
    if len(active) >= 2:
        return {
            "timestamp": datetime.utcnow(),
            "sensors": active,
            "details": events
        }
    return None

# single sensor alert
def single_alert(event_type, data):
    print("\n|| === SINGLE-SENSOR ALERT === ||")
    print(f"Sensor: {event_type}")
    print(f"Time: {data['timestamp']}")
    print(json.dumps(data, indent=2, default=str))
    print("=================================\n")

# multi sensor correlation alert
def correlation_alert(corr):
    print("\n|| === MULTI-SENSOR SPACE EVENT DETECTED === ||")
    print(f"Time: {corr['timestamp']}")
    print(f"Sensors involved: {corr['sensors']}")
    print(f"Details: {corr['details']}")
    print("================================================\n")

def App():
    print("[INFO] SPACE WEATHER ENGINE INITIATED...")
    print("[INFO] Listening for solar flares and solar wind shocks...")

    running = True
    while running:
        flare = get_solar_flare_data()
        flare_event = detect_solar_flare_spike(flare)

        wind = get_solar_wind_data()
        wind_event = detect_solar_wind_shock(wind)

        if not any([flare_event, wind_event]):
            print("[INFO] SLEEP MODE INITIATED: No anomalies detected...")
            print("[SLEEP MODE] Sleeping for 60 seconds...\n")
            time.sleep(60)
            continue

        events = {
            "solar_flare": flare if flare_event else None,
            "solar_wind": wind if wind_event else None
        }

        if flare_event:
            single_alert("[WARNING] SOLAR FLARE DETECTED", flare)

        if wind_event:
            single_alert("[WARNING] SOLAR WIND SHOCK DETECTED", wind)

        correlation = correlate_events(events)
        if correlation:
            correlation_alert(correlation)

        time.sleep(30)

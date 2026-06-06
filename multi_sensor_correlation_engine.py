import time
import requests
from datetime import datetime, timezone
import json

# retrieve Seismic data --> earthquakes
def get_seismic_data():
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_minute.geojson"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        feats = data.get("features", [])
        if not feats:
            return None

        strongest = max(feats, key=lambda f: f["properties"].get("mag") or 0.0)
        props = strongest["properties"]

        mag = props.get("mag")
        place = props.get("place", "Unknown location")
        time_ms = props.get("time")

        if mag is None or time_ms is None:
            return None

        ts = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)

        return {
            "timestamp": ts,
            "magnitude": float(mag),
            "place": place
        }

    except Exception:
        return None

# retrieve Geomagnetic data --> planetary data
def get_geomagnetic_data():
    try:
        url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        if not data:
            return None

        latest = data[-1]
        kp = latest.get("kp_index")
        time_str = latest.get("time_tag")

        if kp is None or time_str is None:
            return None

        ts = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

        return {
            "timestamp": ts,
            "kp_index": float(kp),
            "time_tag": f"Planetary Kp Index: {kp}"
        }

    except Exception:
        return None

def get_cosmic_ray_data():
    try:
        url = "https://cosmicrays.oulu.fi/monitor.txt"
        res = requests.get(url)
        res.raise_for_status()

        lines = res.text.split("\n")

        # the last line contains the latest measurement --> capture it
        for line in reversed(lines):
            if line.strip():
                last = line.split()
                break

        year, month, day = map(int, last[0:3])
        hour, minute = map(int, last[3:5])
        neutron_count = float(last[5])

        ts = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)

        return {
            "timestamp": ts,
            "neutron_count": neutron_count
        }

    except Exception:
        return None


# anomaly detector for seismic activity --> detect seismic spikes
def detect_seismic_spike(data):
    return data and data["magnitude"] >= 1.0

# anomaly detector for geomagnetic activity --> detect planetary spikes
def detect_geomagnetic_spike(data):
    return data and data["kp_index"] >= 3

# anomaly detector for Cosmic Ray activity --> detect cosmic rays
def detect_cosmic_ray_spike(data):
    return data and data["neutron_count"] < 6400

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
    print("\n|| === MULTI-SENSOR CORRELATION DETECTED === ||")
    print(f"Time: {corr['timestamp']}")
    print(f"Sensors involved: {corr['sensors']}")
    print(f"Details: {corr['details']}")
    print("================================================\n")

def main():
    print("[INFO] MULTI-SENSOR CORRELATION ENGINE INITIATED...")
    print("[INFO] Listening for anomalies...\n")

    running = True
    while running:
        seismic = get_seismic_data()
        geomagnetic = get_geomagnetic_data()

        seismic_event = detect_seismic_spike(seismic)
        geomagnetic_event = detect_geomagnetic_spike(geomagnetic)

        cosmicray = get_cosmic_ray_data()
        cosmic_event = detect_cosmic_ray_spike(cosmicray)

        if not any([seismic_event, geomagnetic_event, cosmic_event]):
            print("[INFO] SLEEP MODE INITIATED: No anomalies detected...")
            print("[SLEEP MODE] Sleeping for 10 seconds...")
            time.sleep(10)
            continue

        events = {
            "seismic": seismic if seismic_event else None,
            "geomagnetic": geomagnetic if geomagnetic_event else None,
            "cosmic_rays": cosmicray if cosmic_event else None
        }

        if seismic_event:
            single_alert("[WARNING] SEISMIC ACTIVITY SPIKE", seismic)

        if geomagnetic_event:
            single_alert("[WARNING] GEOMAGNETIC DISTURBANCE DETECTED", geomagnetic)

        if cosmic_event:
            single_alert("[WARNING] COSMIC RAY ANOMALY DETECTED", cosmicray)

        correlation = correlate_events(events)
        if correlation:
            correlation_alert(correlation)

        time.sleep(5)

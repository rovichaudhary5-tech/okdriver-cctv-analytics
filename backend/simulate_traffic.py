import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Sequence of synthetic camera detections
# 1. Normal vehicle (no watchlist match)
# 2. Blacklisted vehicle at Camera C001 (triggers alert)
# 3. Same vehicle detected later at Camera C002 (triggers GIS trajectory correlation)
test_events = [
    {
        "camera_id": "C003",
        "event_type": "ANPR",
        "vehicle_number": "GJ01AB9999",
        "confidence": 0.91,
        "vehicle_type": "Sedan"
    },
    {
        "camera_id": "C001",
        "event_type": "ANPR",
        "vehicle_number": "GJ01XX0001",  # Matches STOLEN_VEHICLE on Watchlist!
        "confidence": 0.97,
        "vehicle_type": "SUV"
    },
    {
        "camera_id": "C002",
        "event_type": "ANPR",
        "vehicle_number": "GJ01XX0001",  # Same stolen car seen at Checkpoint 2
        "confidence": 0.94,
        "vehicle_type": "SUV"
    }
]

print("--- Starting AI CCTV Event Simulation ---")

for idx, evt in enumerate(test_events, 1):
    print(f"\n[Event {idx}] Sending detection for plate: {evt['vehicle_number']} at {evt['camera_id']}...")
    try:
        response = requests.post(f"{BASE_URL}/analytics/ingest", json=evt)
        res_data = response.json()
        print(f"Status: {res_data.get('status')} | Watchlist Matched: {res_data.get('matched')}")
        if res_data.get("matched"):
            alert = res_data.get("alert")
            print(f"🚨 ALERT GENERATED: {alert['id']} ({alert['category']}) - Severity: {alert['severity']}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")
    
    time.sleep(3)

print("\n--- Simulation Complete. Check your Web Dashboard! ---")
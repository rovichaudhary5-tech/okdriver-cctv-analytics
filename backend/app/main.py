from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os

app = FastAPI(
    title="okDriver Unified CCTV & Analytics Platform",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static directory setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

cameras_db = {
    "C001": {
        "id": "C001",
        "name": "SG Highway Junction 4, Ahmedabad",
        "department": "Traffic Police",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "camera_type": "PTZ 4K",
        "source_protocol": "RTSP",
        "stream_endpoint": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "status": "Online",
        "zone": "Ahmedabad West",
        "last_heartbeat": datetime.datetime.now(datetime.timezone.utc).isoformat()
    },
    "C002": {
        "id": "C002",
        "name": "RTO Checkpoint Gandhinagar",
        "department": "RTO Gujarat",
        "latitude": 23.2156,
        "longitude": 72.6369,
        "camera_type": "Fixed ANPR",
        "source_protocol": "RTSP",
        "stream_endpoint": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "status": "Online",
        "zone": "Gandhinagar Outer",
        "last_heartbeat": datetime.datetime.now(datetime.timezone.utc).isoformat()
    },
    "C003": {
        "id": "C003",
        "name": "Sarkhej Cross Road",
        "department": "Traffic Police",
        "latitude": 22.9868,
        "longitude": 72.4996,
        "camera_type": "Fixed Bullet",
        "source_protocol": "HLS",
        "stream_endpoint": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "status": "Degraded",
        "zone": "Ahmedabad South",
        "last_heartbeat": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
}

watchlist_db = {
    "GJ01XX0001": {
        "identifier": "GJ01XX0001",
        "entity_type": "VEHICLE",
        "category": "STOLEN_VEHICLE",
        "severity": "CRITICAL",
        "notes": "Reported stolen at Vastrapur PS. FIR #402/2026"
    },
    "GJ05AB1234": {
        "identifier": "GJ05AB1234",
        "entity_type": "VEHICLE",
        "category": "BLACKLISTED",
        "severity": "HIGH",
        "notes": "Repeated red-light violator & unpaid e-challans"
    }
}

events_log = []
alerts_log = []

class AIEventInput(BaseModel):
    camera_id: str
    event_type: str
    vehicle_number: Optional[str] = None
    confidence: float
    vehicle_type: Optional[str] = "Sedan"
    bounding_box: Optional[dict] = {"x": 100, "y": 150, "w": 200, "h": 80}

class AlertResolution(BaseModel):
    status: str
    operator_notes: str

@app.get("/", include_in_schema=False)
def serve_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "service": "okDriver Unified CCTV Platform"}

@app.get("/api/v1/cameras")
def get_cameras():
    return list(cameras_db.values())

@app.post("/api/v1/cameras")
async def register_camera(camera: dict):
    cameras_db[camera["id"]] = camera
    await ws_manager.broadcast({"type": "CAMERA_REGISTERED", "data": camera})
    return {"status": "success", "camera": camera}

@app.get("/api/v1/watchlist")
def get_watchlist():
    return list(watchlist_db.values())

@app.post("/api/v1/analytics/ingest")
async def ingest_ai_event(payload: AIEventInput):
    camera = cameras_db.get(payload.camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera ID not found")

    event_id = f"EVT-{len(events_log) + 1:05d}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clean_number = payload.vehicle_number.upper().strip() if payload.vehicle_number else None

    is_match = clean_number in watchlist_db if clean_number else False
    
    event_entry = {
        "id": event_id,
        "camera_id": payload.camera_id,
        "camera_name": camera["name"],
        "latitude": camera["latitude"],
        "longitude": camera["longitude"],
        "event_type": payload.event_type,
        "vehicle_number": clean_number,
        "vehicle_type": payload.vehicle_type,
        "confidence": payload.confidence,
        "bounding_box": payload.bounding_box,
        "timestamp": timestamp,
        "is_watchlist_match": is_match
    }
    events_log.append(event_entry)

    alert_entry = None
    if is_match:
        target = watchlist_db[clean_number]
        alert_id = f"ALT-{len(alerts_log) + 1:05d}"
        alert_entry = {
            "id": alert_id,
            "event_id": event_id,
            "camera_id": payload.camera_id,
            "camera_name": camera["name"],
            "latitude": camera["latitude"],
            "longitude": camera["longitude"],
            "matched_identifier": clean_number,
            "category": target["category"],
            "severity": target["severity"],
            "notes": target["notes"],
            "status": "ACTIVE",
            "confidence": payload.confidence,
            "timestamp": timestamp
        }
        alerts_log.append(alert_entry)
        
        await ws_manager.broadcast({
            "type": "NEW_ALERT",
            "data": alert_entry
        })

    await ws_manager.broadcast({
        "type": "NEW_DETECTION",
        "data": event_entry
    })

    return {
        "status": "processed",
        "matched": is_match,
        "alert": alert_entry
    }

@app.get("/api/v1/alerts")
def get_alerts():
    return sorted(alerts_log, key=lambda x: x["timestamp"], reverse=True)

@app.patch("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, res: AlertResolution):
    for alert in alerts_log:
        if alert["id"] == alert_id:
            alert["status"] = res.status
            alert["operator_notes"] = res.operator_notes
            await ws_manager.broadcast({"type": "ALERT_UPDATED", "data": alert})
            return {"status": "updated", "alert": alert}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.get("/api/v1/entities/trace")
def trace_entity(identifier: str):
    matches = [e for e in events_log if e.get("vehicle_number") == identifier.upper()]
    matches.sort(key=lambda x: x["timestamp"])
    return {
        "identifier": identifier,
        "detection_count": len(matches),
        "history": matches
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
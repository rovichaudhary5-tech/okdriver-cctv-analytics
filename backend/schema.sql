CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Camera Registry
CREATE TABLE cameras (
    id VARCHAR(50) PRIMARY KEY, -- e.g., 'C001'
    name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL, -- Traffic, Municipal, Port, RTO
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    camera_type VARCHAR(50) DEFAULT 'Fixed Bullet', -- PTZ, Dome, Fixed
    source_protocol VARCHAR(20) DEFAULT 'RTSP', -- RTSP, ONVIF, HLS, WebRTC
    stream_endpoint TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'Online', -- Online, Offline, Degraded
    zone VARCHAR(100) NOT NULL,
    storage_metadata JSONB DEFAULT '{}'::jsonb,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Watchlist Records
CREATE TABLE watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- VEHICLE, PERSON
    identifier VARCHAR(100) NOT NULL UNIQUE, -- e.g., 'GJ01XX0001'
    category VARCHAR(50) NOT NULL, -- STOLEN, BLACKLISTED, WANTED, SUSPECT
    severity VARCHAR(20) DEFAULT 'HIGH', -- CRITICAL, HIGH, MEDIUM, LOW
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. AI Detections / Analytics Events
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id VARCHAR(50) REFERENCES cameras(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- ANPR, VEHICLE_DETECTION, PERSON_DETECTION
    detected_identifier VARCHAR(100), -- 'GJ01XX0001'
    vehicle_type VARCHAR(50), -- Sedan, Truck, SUV, Two-Wheeler
    confidence DOUBLE PRECISION NOT NULL,
    bounding_box JSONB, -- {"x": 120, "y": 240, "w": 80, "h": 40}
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_watchlist_match BOOLEAN DEFAULT FALSE
);

-- 4. Real-time Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES analytics_events(id) ON DELETE CASCADE,
    watchlist_id UUID REFERENCES watchlist(id) ON DELETE SET NULL,
    camera_id VARCHAR(50) REFERENCES cameras(id),
    matched_identifier VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, ACKNOWLEDGED, RESOLVED
    operator_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_events_identifier ON analytics_events(detected_identifier);
CREATE INDEX idx_events_timestamp ON analytics_events(timestamp DESC);
CREATE INDEX idx_cameras_status ON cameras(status);
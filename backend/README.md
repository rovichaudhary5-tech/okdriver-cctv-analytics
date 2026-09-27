# okDriver - CCTV Monitoring & Video Analytics Platform

A centralized CCTV monitoring and video analytics platform prototype built for the okDriver hiring challenge and aligned with the Gujarat Police Innovation Hackathon 2026.

## Features
- **Camera Registry & GIS Mapping**: Interactive Leaflet map displaying camera health, zone, and real-time status.
- **Unified Operator Console**: Live CCTV grid monitoring alongside real-time AI detection streams.
- **ANPR & Watchlist Correlation**: Automatic correlation of incoming detection events against stolen/blacklisted vehicle registries.
- **Real-Time Push Alerts**: Instant WebSocket-based alert broadcasting without page refresh.
- **GIS Vehicle Route Reconstruction**: Historical route reconstruction connecting sequential camera detections with map polylines.

## Quick Start Guide

### Prerequisites
- Python 3.10+ installed

### Setup & Run
1. Clone the repository and enter the backend folder:
   ```bash
   cd backend
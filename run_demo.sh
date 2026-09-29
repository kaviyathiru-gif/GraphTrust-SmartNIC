#!/usr/bin/env bash
set -e

echo "=== TrustNet-SDN Platform Demonstration Runner ==="
echo "Starting FastAPI Server and WebSocket Telemetry Broker..."

export PYTHONPATH=$(pwd)
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

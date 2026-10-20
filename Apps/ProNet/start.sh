#!/usr/bin/env bash
set -e

echo "====================================================================="
echo "             ProNet Professional Network - Local Launch"
echo "====================================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Checking dependencies..."
python3 -m pip install -r src/backend/requirements.txt -q

echo "[2/3] Seeding database..."
cd src/backend
python3 seed_data.py
cd "$SCRIPT_DIR"

echo "[3/3] Starting services..."
cd src/backend
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cd "$SCRIPT_DIR/src/frontend"
npm run dev &
FRONTEND_PID=$!

echo "ProNet running!"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"

wait

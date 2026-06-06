#!/bin/bash
set -e

echo "═══════════════════════════════════════"
echo "  NUTRITION TRACKER — Web Application  "
echo "═══════════════════════════════════════"

# Install frontend deps if needed
if [ ! -d "web/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd web && npm install)
fi

# Start FastAPI backend on port 8080
echo "Starting API server (port 8080)..."
uvicorn src.web.api:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!

cleanup() {
    kill $BACKEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM EXIT

# Give backend a moment to start
sleep 2

# Start Vite frontend on port 5173 (foreground)
echo "Starting web frontend (port 5000)..."
cd web && npm run dev

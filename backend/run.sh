#!/bin/bash

# Voice Agent Backend Runner
# Runs the FastAPI backend with uvicorn

cd "$(dirname "$0")/.."

echo "🚀 Starting Voice Agent Backend..."
echo ""

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

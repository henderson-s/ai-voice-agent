#!/bin/bash
cd "$(dirname "$0")/.."
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000


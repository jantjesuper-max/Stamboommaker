#!/bin/sh
# Start de stamboomwebsite en open de browser (macOS/Linux).
cd "$(dirname "$0")" || exit 1
python3 server.py

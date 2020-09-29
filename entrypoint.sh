#!/bin/bash
cd /app/src
if [ ! -f "/app/src/config/settings.json" ]; then
    cp ../sample_settings.json ./config/
fi
python3 main.py

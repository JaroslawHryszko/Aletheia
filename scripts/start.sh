#!/bin/bash
echo "🔁 Uruchamianie Alethei – API serwera..."
uvicorn aletheia.api.main:app --host 0.0.0.0 --port 8000 --reload

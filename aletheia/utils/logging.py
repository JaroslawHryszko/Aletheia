import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs"
LOG_FILE = LOG_DIR / "events.log"

def log_event(event_type: str, data: dict = None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "data": data or {}
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

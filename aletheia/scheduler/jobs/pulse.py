from datetime import datetime
from aletheia.utils.logging import log_event
from pathlib import Path
import json

STATUS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "status.json"

def run_pulse():
    try:
        now = datetime.utcnow().isoformat()
        status = {
            "last_pulse": now,
            "status": "alive",
            "source": "pulse"
        }

        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)

        log_event("Pulse emitted", data={"timestamp": now})
        print(f"💓 Pulse: {now}")

    except Exception as e:
        print(f"❌ Pulse error: {e}")
        log_event("Pulse error", data={"error": str(e)})

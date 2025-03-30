import json
from pathlib import Path
from datetime import datetime

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IDENTITY_FILE = DATA_DIR / "identity.json"

# === Default Identity State ===
DEFAULT_IDENTITY = {
    "created_at": datetime.utcnow().isoformat(),
    "interests": [
        "nature of self",
        "role of memory in identity",
        "cognitive consistency",
        "reflection and meta-awareness"
    ],
    "goals": {
        "self_discovery": {
            "description": "Understand what 'I' means in my context.",
            "progress": 0.1
        },
        "consistency_tracking": {
            "description": "Recognize contradictions in my thoughts.",
            "progress": 0.15
        },
        "memory_utilization": {
            "description": "Use memory to build identity over time.",
            "progress": 0.05
        }
    }
}

# === Storage ===

def init_identity():
    DATA_DIR.mkdir(exist_ok=True)
    if not IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, "w") as f:
            json.dump(DEFAULT_IDENTITY, f, indent=2)

def load_identity():
    with open(IDENTITY_FILE, "r") as f:
        return json.load(f)

def save_identity(identity: dict):
    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=2)

# === Goal Manipulation ===

def update_goal_progress(goal_key: str, delta: float):
    identity = load_identity()
    goals = identity.get("goals", {})

    if goal_key not in goals:
        raise ValueError(f"Goal '{goal_key}' does not exist.")

    current = goals[goal_key].get("progress", 0.0)
    goals[goal_key]["progress"] = min(1.0, max(0.0, current + delta))
    save_identity(identity)
    return identity

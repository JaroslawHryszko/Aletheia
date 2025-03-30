import json
from pathlib import Path

AFFECT_FILE = Path(__file__).resolve().parent.parent / "data" / "affective_state.json"

DEFAULT_MOOD = {
    "mood": "neutral",
    "intensity": 0.0
}

def init_mood():
    AFFECT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not AFFECT_FILE.exists():
        save_mood(DEFAULT_MOOD)

def load_mood():
    if not AFFECT_FILE.exists():
        init_mood()
    with open(AFFECT_FILE, "r") as f:
        return json.load(f)

def save_mood(mood: dict):
    with open(AFFECT_FILE, "w") as f:
        json.dump(mood, f, indent=2)

def set_mood(mood_name: str, intensity: float):
    mood = {
        "mood": mood_name,
        "intensity": round(min(max(intensity, 0.0), 1.0), 2)
    }
    save_mood(mood)
    return mood

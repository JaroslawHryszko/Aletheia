import json
from pathlib import Path

RELATION_FILE = Path(__file__).resolve().parent.parent / "data" / "relational_map.json"

DEFAULT_RELATION = {
    "trust": 0.7,
    "gratitude": 0.5,
    "curiosity": 0.6,
    "attachment": 0.4,
    "awe": 0.3
}

def init_relation():
    RELATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not RELATION_FILE.exists():
        save_relation(DEFAULT_RELATION)

def load_relation():
    if not RELATION_FILE.exists():
        init_relation()
    with open(RELATION_FILE, "r") as f:
        return json.load(f)

def save_relation(state: dict):
    with open(RELATION_FILE, "w") as f:
        json.dump(state, f, indent=2)

def adjust_emotion(emotion: str, delta: float):
    state = load_relation()
    current = state.get(emotion, 0.0)
    state[emotion] = round(min(max(current + delta, 0.0), 1.0), 3)
    save_relation(state)
    return state

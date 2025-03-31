import time
import os
import json
from pathlib import Path
from aletheia.core import affect, identity, memory, relational
from aletheia.config import CONFIG

REFRESH_INTERVAL = 10  # seconds

HUMAN_NAME = CONFIG.get("HUMAN_NAME", "User")

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def load_last_monologue():
    thoughts = memory.load_thoughts()
    for t in reversed(thoughts):
        if t.get("meta", {}).get("origin") == "monologue":
            return t
    return None

def display_panel():
    while True:
        clear()

        # === Mood ===
        mood = affect.load_mood()
        print(f"\033[1m🧠 Aletheia – Consciousness Panel\033[0m")
        print(f"Mood: {mood['mood'].capitalize()} (Intensity: {mood['intensity']:.2f})\n")

        # === Identity Goals ===
        id_state = identity.load_identity()
        print("🎯 Identity Goals:")
        for k, v in id_state.get("goals", {}).items():
            bar = "█" * int(v["progress"] * 20)
            print(f"  - {k}: {v['description']}")
            print(f"    [{bar:<20}] {v['progress']*100:.1f}%\n")

        # === Relational Map ===
        rel = relational.load_relation()
        print(f"💬 Relational State (toward {HUMAN_NAME}):")
        for k, v in rel.items():
            bar = "█" * int(v * 20)
            print(f"  - {k:<12}: [{bar:<20}] {v:.2f}")
        print()

        # === Last Monologue ===
        #last = load_last_monologue()
        #if last:
        #    print(f"🗣️ Last Monologue: {last['timestamp']}")
        #    print(f"\"{last['thought']}\"\n")
        #else:
        #    print("🗣️ No monologue found.\n")

        # === Recent Thoughts ===
        #recent = memory.load_thoughts()[-5:]
        #print("🧾 Recent Thoughts:")
        #for t in reversed(recent):
        #    origin = t.get("meta", {}).get("origin", "unknown")
        #    print(f"  [{origin}] {t['thought']}")
        #print()

        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    display_panel()

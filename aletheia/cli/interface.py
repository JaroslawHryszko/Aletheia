import requests
import os
import time
from aletheia.config import CONFIG

BASE_URL = os.getenv("ALETHEIA_API", "http://localhost:8000")

AGENT_NAME = CONFIG.get("AGENT_NAME", "Aletheia")

def ask_oracle():
    prompt = input(f"\n🧠 Ask {AGENT_NAME} a question: ")
    payload = {
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 300
    }
    try:
        response = requests.post(f"{BASE_URL}/oracle", json=payload)
        response.raise_for_status()
        print(f"\n🔮 Reply: {response.json()['reply']}\n")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_monologue():
    try:
        response = requests.get(f"{BASE_URL}/monologue")
        response.raise_for_status()
        data = response.json()
        print(f"\n🗣️ Latest monologue ({data['timestamp']}):\n\"{data['thought']}\"\n")
    except:
        print("⚠️ No monologue available.")

def show_recent_thoughts():
    try:
        response = requests.get(f"{BASE_URL}/thoughts/recent?limit=5")
        response.raise_for_status()
        print("\n🧾 Recent thoughts:")
        for t in reversed(response.json()):
            print(f"[{t['meta'].get('origin', '---')}] {t['thought']}")
        print()
    except:
        print("⚠️ Failed to retrieve thoughts.")

def add_shadow():
    print("\n✍️ Adding an entry to the Shadow Book.")
    content = input("Content: ")
    cause = input("Cause (optional): ")
    payload = {"content": content, "cause": cause or "unspecified"}
    try:
        response = requests.post(f"{BASE_URL}/shadow", json=payload)
        response.raise_for_status()
        print("📓 Entry saved to shadow.\n")
    except:
        print("❌ Failed to save the entry.")

def show_identity_goals():
    try:
        response = requests.get(f"{BASE_URL}/identity")
        response.raise_for_status()
        data = response.json().get("goals", {})
        print(f"\n🎯 {AGENT_NAME}'s Identity Goals:")
        for k, v in data.items():
            bar = "█" * int(v["progress"] * 20)
            print(f"- {k}: {v['description']}")
            print(f"  [{bar:<20}] {v['progress'] * 100:.1f}%\n")
    except:
        print("⚠️ No goals found or connection error.")

def main():
    while True:
        print(f"=== {AGENT_NAME} INTERFACE ===")
        print(f"1. Ask {AGENT_NAME} a question (oracle)")
        print("2. Read the latest monologue")
        print("3. View recent thoughts")
        print("4. Add an entry to the Shadow Book")
        print("5. Show identity goals")
        print("6. Exit")
        choice = input("Choose an option [1–6]: ").strip()

        if choice == "1":
            ask_oracle()
        elif choice == "2":
            show_monologue()
        elif choice == "3":
            show_recent_thoughts()
        elif choice == "4":
            add_shadow()
        elif choice == "5":
            show_identity_goals()
        elif choice == "6":
            print(f"\n👋 Ending session with {AGENT_NAME}. See you later.\n")
            break
        else:
            print("Invalid choice. Please try again.\n")

        time.sleep(1)

if __name__ == "__main__":
    main()
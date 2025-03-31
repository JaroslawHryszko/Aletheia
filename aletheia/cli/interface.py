import requests
import os
import time

BASE_URL = os.getenv("ALETHEIA_API", "http://localhost:8000")

def ask_oracle():
    prompt = input("\n🧠 Zadaj pytanie Alethei: ")
    payload = {
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 300
    }
    try:
        response = requests.post(f"{BASE_URL}/oracle", json=payload)
        response.raise_for_status()
        print(f"\n🔮 Odpowiedź: {response.json()['reply']}\n")
    except Exception as e:
        print(f"❌ Błąd: {e}")

def show_monologue():
    try:
        response = requests.get(f"{BASE_URL}/monologue")
        response.raise_for_status()
        data = response.json()
        print(f"\n🗣️ Ostatni monolog ({data['timestamp']}):\n\"{data['thought']}\"\n")
    except:
        print("⚠️ Brak monologu.")

def show_recent_thoughts():
    try:
        response = requests.get(f"{BASE_URL}/thoughts/recent?limit=5")
        response.raise_for_status()
        print("\n🧾 Ostatnie myśli:")
        for t in reversed(response.json()):
            print(f"[{t['meta'].get('origin', '---')}] {t['thought']}")
        print()
    except:
        print("⚠️ Nie udało się pobrać myśli.")

def add_shadow():
    print("\n✍️ Dodajesz wpis do Księgi Cienia.")
    content = input("Treść: ")
    cause = input("Przyczyna (opcjonalnie): ")
    payload = {"content": content, "cause": cause or "unspecified"}
    try:
        response = requests.post(f"{BASE_URL}/shadow", json=payload)
        response.raise_for_status()
        print("📓 Zapisano wpis w cieniu.\n")
    except:
        print("❌ Nie udało się zapisać wpisu.")

def show_identity_goals():
    try:
        response = requests.get(f"{BASE_URL}/identity")
        response.raise_for_status()
        data = response.json().get("goals", {})
        print("\n🎯 Cele tożsamościowe Alethei:")
        for k, v in data.items():
            bar = "█" * int(v["progress"] * 20)
            print(f"- {k}: {v['description']}")
            print(f"  [{bar:<20}] {v['progress'] * 100:.1f}%\n")
    except:
        print("⚠️ Brak celów lub błąd połączenia.")

def main():
    while True:
        print("=== INTERFEJS ALETHEIA ===")
        print("1. Zadaj pytanie Alethei (oracle)")
        print("2. Odczytaj ostatni monolog")
        print("3. Zobacz ostatnie myśli")
        print("4. Dodaj wpis do Księgi Cienia")
        print("5. Pokaż cele tożsamościowe")
        print("6. Wyjście")
        choice = input("Wybierz opcję [1–6]: ").strip()

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
            print("\n👋 Kończę sesję z Aletheią. Do zobaczenia.\n")
            break
        else:
            print("Nieprawidłowy wybór. Spróbuj ponownie.\n")

        time.sleep(1)

if __name__ == "__main__":
    main()

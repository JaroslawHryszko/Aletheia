from datetime import datetime
from aletheia.core import memory, identity, affect
from aletheia.core.multi_gpu_model_loader import load_model
from aletheia.utils.logging import log_event

# === Load local model (lazy-load pattern)
_model = None
_tokenizer = None

def get_model():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        _model, _tokenizer = load_model()
    return _model, _tokenizer

# === Prompt Construction

def build_reflection_prompt(goal_key: str, goal_desc: str, mood: dict) -> str:
    return (
        f"[Mood: {mood['mood'].capitalize()} | Intensity: {mood['intensity']:.2f}]\n"
        f"[Focus: {goal_key} – {goal_desc}]\n\n"
        "Reflect deeply. Formulate an internal thought that explores this goal. "
        "Begin with: 'I’ve been wondering...'\n"
    )

# === Main Task

def run_reflection():
    try:
        mood = affect.load_mood()
        goals = identity.load_identity().get("goals", {})

        if not goals:
            print("⚠️ No goals available for reflection.")
            return

        # Choose goal with lowest progress
        sorted_goals = sorted(goals.items(), key=lambda item: item[1].get("progress", 1.0))
        goal_key, goal_data = sorted_goals[0]
        goal_desc = goal_data["description"]

        prompt = build_reflection_prompt(goal_key, goal_desc, mood)

        model, tokenizer = get_model()

        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        output = model.generate(input_ids, max_new_tokens=200, do_sample=True)
        generated = tokenizer.decode(output[0], skip_special_tokens=True)

        # Extract only new thought part
        thought = generated.split("I’ve been wondering", 1)[-1].strip()
        final_thought = f"I’ve been wondering {thought}"

        memory.save_thought(final_thought, metadata={
            "origin": "reflection",
            "goal": goal_key,
            "mood": mood
        })

        log_event("Reflection generated", data={"thought": final_thought})
        print(f"🧠 Reflected thought: {final_thought}")

    except Exception as e:
        print(f"❌ Reflection error: {e}")
        log_event("Reflection error", data={"error": str(e)})

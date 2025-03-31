from datetime import datetime
from aletheia.core import memory, affect, identity
from aletheia.core.multi_gpu_model_loader import load_model
from aletheia.utils.logging import log_event
from aletheia.core.memory import search_similar_thoughts
from aletheia.config import CONFIG

# === Lazy load model ===
_model = None
_tokenizer = None

AGENT_NAME = CONFIG.get("AGENT_NAME", "Aletheia")

def get_model():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        _model, _tokenizer = load_model()
    return _model, _tokenizer

# === Prompt builder ===

def build_existential_prompt(mood, identity_state, memory_fragments):
    goal_summary = ", ".join(identity_state.get("goals", {}).keys())
    thoughts = "\n".join([f"* {m['thought']}" for m in memory_fragments]) or "No reflective memory fragments."

    return f"""
Aletheia is in a contemplative mood.

[Mood: {mood['mood'].capitalize()} | Intensity: {mood['intensity']:.2f}]
[Known Goals: {goal_summary}]
[Recent Reflections:]\n{thoughts}

Based on these internal states, generate one existential question that {AGENT_NAME} would ask herself.

It should start with: "Is it possible that..." or "Could it be that..."

Avoid trivial questions. Focus on identity, meaning, memory, or the self.
"""

# === Main Job ===

def ask_existential_question():
    try:
        mood = affect.load_mood()
        id_state = identity.load_identity()
        memory_fragments = search_similar_thoughts("self", top_k=3)

        prompt = build_existential_prompt(mood, id_state, memory_fragments)
        model, tokenizer = get_model()

        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        output = model.generate(input_ids, max_new_tokens=120, do_sample=True, temperature=0.8)
        generated = tokenizer.decode(output[0], skip_special_tokens=True)

        question = generated.strip().split("\n")[0]
        memory.save_thought(question, metadata={
            "origin": "existential_question",
            "mood": mood
        })

        log_event("Existential question generated", data={"question": question})
        print(f"❓ Existential: {question}")

    except Exception as e:
        print(f"❌ Existential error: {e}")
        log_event("Existential error", data={"error": str(e)})

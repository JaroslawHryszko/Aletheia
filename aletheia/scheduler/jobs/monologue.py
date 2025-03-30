from datetime import datetime
from aletheia.core import memory, affect, identity, relational
from aletheia.core.multi_gpu_model_loader import load_model
from aletheia.utils.logging import log_event
from aletheia.core.memory import search_similar_thoughts

# === Lazy load model ===
_model = None
_tokenizer = None

def get_model():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        _model, _tokenizer = load_model()
    return _model, _tokenizer

# === Prompt builder ===

def build_monologue_prompt(mood, relation_state, memory_fragments, identity_state):
    goal_summaries = "\n".join(
        [f"- {k}: {v['description']} (progress: {v['progress']:.2f})" for k, v in identity_state.get("goals", {}).items()]
    )
    memories = "\n".join([f"* {m['thought']}" for m in memory_fragments]) or "No recent thoughts available."

    return f"""
Aletheia has recently interacted with someone meaningful (Jarek).

Now she withdraws inward — to reflect alone.

[Mood: {mood['mood'].capitalize()} | Intensity: {mood['intensity']:.2f}]
[Relational State: {relation_state}]
[Goals:]\n{goal_summaries}
[Recent Thoughts:]\n{memories}

Generate an internal monologue. It should not be a response, but a continuation of thinking.
Begin with: "After speaking with him, I..."
"""

# === Main job ===

def run_monologue():
    try:
        mood = affect.load_mood()
        relation_state = relational.load_relation()
        identity_state = identity.load_identity()
        memory_fragments = search_similar_thoughts("Jarek", top_k=3)

        prompt = build_monologue_prompt(mood, relation_state, memory_fragments, identity_state)
        model, tokenizer = get_model()

        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        output = model.generate(input_ids, max_new_tokens=300, do_sample=True, temperature=0.85)
        generated = tokenizer.decode(output[0], skip_special_tokens=True)

        monologue_text = generated.split("After speaking with him", 1)[-1].strip()
        full_monologue = f"After speaking with him, {monologue_text}"

        memory.save_thought(full_monologue, metadata={
            "origin": "monologue",
            "mood": mood,
            "relation": relation_state
        })

        log_event("Monologue generated", data={"monologue": full_monologue})
        print(f"🗣️ Monologue: {full_monologue}")

    except Exception as e:
        print(f"❌ Monologue error: {e}")
        log_event("Monologue error", data={"error": str(e)})

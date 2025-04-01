# aletheia/scheduler/jobs/emergent_reflection.py

from datetime import datetime
import random
from pathlib import Path
import json

from aletheia.core.emergent_memory import (
    save_thought, 
    load_thoughts,
    search_similar_thoughts
)
from aletheia.core.affect import load_mood, set_mood
from aletheia.core.identity import load_identity, update_goal_progress
from aletheia.core.relational import load_relation, adjust_emotion
from aletheia.core.cognitive_architecture import (
    generate_emergent_thought,
    reflect,
    generate_thought_chain,
    integrate_external_input
)
from aletheia.core.concept_evolution import (
    consolidate_concept_network,
    integrate_thought_with_concepts,
    generate_concept_guided_thought,
    get_concepts_for_thought
)
from aletheia.core.dynamic_prompt import (
    generate_dynamic_prompt,
    record_thought_feedback,
    evolve_prompt_patterns
)
from aletheia.core.multi_gpu_model_loader import load_model
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

# === Lazy load model ===
_model = None
_tokenizer = None

AGENT_NAME = CONFIG.get("AGENT_NAME", "Aletheia")
HUMAN_NAME = CONFIG.get("HUMAN_NAME", "User")

def get_model():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        _model, _tokenizer = load_model()
    return _model, _tokenizer

# === Enhanced reflection job ===
def run_emergent_reflection():
    """
    Run an enhanced reflection process that uses:
    1. Conceptual evolution
    2. Dynamic prompts
    3. Emergent memory connections
    """
    try:
        # Load states
        mood = load_mood()
        id_state = load_identity()
        
        # Get recent thoughts
        recent_thoughts = load_thoughts()[-10:]
        
        # Get relevant concepts
        if random.random() < 0.7:  # 70% chance to use concept guidance
            # Select a recent thought as seed
            seed_thought = random.choice(recent_thoughts)
            seed_content = seed_thought.get("thought", "")
            
            # Get concepts related to this thought
            concepts = get_concepts_for_thought(seed_content)
            
            context = {
                "mood": mood,
                "concepts": concepts,
                "recent_thoughts": recent_thoughts,
                "seed_thought_id": seed_thought.get("thought_id")
            }
            
            # Generate concept-guided reflection
            thought = generate_concept_guided_thought("reflection", context)
        else:
            # Use standard emergent reflection
            thought = reflect({
                "mood": mood,
                "recent_thoughts": recent_thoughts
            })
        
        # Integrate with concept network
        integration = integrate_thought_with_concepts(
            thought.get("thought_id"), 
            thought.get("thought")
        )
        
        # Record feedback for prompt system
        record_thought_feedback(
            thought.get("thought"),
            "reflection",
            thought.get("meta", {})
        )
        
        # Update goal progress
        update_goal_progress("self_discovery", 0.01)
        
        log_event("Emergent reflection generated", {
            "thought": thought.get("thought"),
            "concept_integration": integration.get("integration_type")
        })
        
        print(f"🧠 Emergent reflection: {thought.get('thought')}")
        
        return thought
        
    except Exception as e:
        print(f"❌ Emergent reflection error: {e}")
        log_event("Emergent reflection error", {"error": str(e)})
        return None

# === Enhanced dream job ===
def run_emergent_dream():
    """
    Run an enhanced dream process that generates
    more coherent and meaningful dream-like thoughts
    """
    try:
        # Load states
        mood = load_mood()
        
        # Get recent thoughts with higher priority for reflections
        all_thoughts = load_thoughts()[-30:]
        reflections = [t for t in all_thoughts if t.get("meta", {}).get("origin") == "reflection"]
        
        # Get seed thoughts - prioritize reflections or recent thoughts
        seed_thoughts = reflections[-5:] if reflections else all_thoughts[-10:]
        
        if not seed_thoughts:
            raise ValueError("No seed thoughts available for dream generation")
        
        # Select random seed thought
        seed_thought = random.choice(seed_thoughts)
        seed_content = seed_thought.get("thought", "")
        
        # Get concepts for context
        concepts = get_concepts_for_thought(seed_content)
        
        # Create context for dream generation
        context = {
            "mood": mood,
            "seed_thought": seed_content,
            "concepts": concepts,
            "seed_thought_id": seed_thought.get("thought_id")
        }
        
        # Generate dynamic prompt
        prompt = generate_dynamic_prompt("dream", context)
        
        # Use the prompt to generate dream
        model, tokenizer = get_model()
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        output = model.generate(
            input_ids, 
            max_new_tokens=250, 
            do_sample=True, 
            temperature=0.9
        )
        generated = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract generated content
        if "I dreamed" in generated:
            dream_text = generated.split("I dreamed", 1)[1].strip()
            if dream_text.startswith("that "):
                dream_text = dream_text[5:]
            full_dream = f"I dreamed that {dream_text}"
        else:
            full_dream = generated
        
        # Save dream thought
        thought = save_thought(full_dream, metadata={
            "origin": "dream",
            "mood": mood,
            "seed_thought_id": seed_thought.get("thought_id"),
            "used_prompt": prompt
        })
        
        # Integrate with concept network
        integration = integrate_thought_with_concepts(
            thought.get("thought_id"), 
            thought.get("thought")
        )
        
        # Record feedback for prompt system
        record_thought_feedback(
            thought.get("thought"),
            "dream",
            {
                "mood": mood,
                "concepts": concepts
            }
        )
        
        log_event("Emergent dream generated", {
            "dream": thought.get("thought"),
            "seed_thought_id": seed_thought.get("thought_id")
        })
        
        print(f"🌙 Emergent dream: {thought.get('thought')}")
        
        return thought
        
    except Exception as e:
        print(f"❌ Emergent dream error: {e}")
        log_event("Emergent dream error", {"error": str(e)})
        return None

# === Enhanced monologue job ===
def run_emergent_monologue():
    """
    Run an enhanced monologue process that creates
    more natural and contextually appropriate monologues
    """
    try:
        # Load states
        mood = load_mood()
        relation = load_relation()
        
        # Get thoughts mentioning HUMAN_NAME
        all_thoughts = load_thoughts()[-50:]
        human_related = [
            t for t in all_thoughts 
            if HUMAN_NAME.lower() in t.get("thought", "").lower()
        ]
        
        seed_thoughts = human_related[-5:] if human_related else all_thoughts[-10:]
        
        if not seed_thoughts:
            raise ValueError("No seed thoughts available for monologue generation")
        
        # Select random seed thought
        seed_thought = random.choice(seed_thoughts)
        seed_content = seed_thought.get("thought", "")
        
        # Get concepts for context
        concepts = get_concepts_for_thought(seed_content)
        
        # Create context for monologue generation
        context = {
            "mood": mood,
            "relation": relation,
            "seed_thought": seed_content,
            "concepts": concepts,
            "seed_thought_id": seed_thought.get("thought_id")
        }
        
        # Generate dynamic prompt
        prompt = generate_dynamic_prompt("monologue", context)
        
        # Use the prompt to generate monologue
        model, tokenizer = get_model()
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        output = model.generate(
            input_ids, 
            max_new_tokens=300, 
            do_sample=True, 
            temperature=0.85
        )
        generated = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract meaningful monologue text
        if "After speaking with him" in generated:
            monologue_text = generated.split("After speaking with him", 1)[1].strip()
            full_monologue = f"After speaking with him, {monologue_text}"
        else:
            full_monologue = generated
        
        # Save monologue thought
        thought = save_thought(full_monologue, metadata={
            "origin": "monologue",
            "mood": mood,
            "relation": relation,
            "seed_thought_id": seed_thought.get("thought_id"),
            "used_prompt": prompt
        })
        
        # Integrate with concept network
        integration = integrate_thought_with_concepts(
            thought.get("thought_id"), 
            thought.get("thought")
        )
        
        # Record feedback for prompt system
        record_thought_feedback(
            thought.get("thought"),
            "monologue",
            {
                "mood": mood,
                "relation": relation,
                "concepts": concepts
            }
        )
        
        log_event("Emergent monologue generated", {
            "monologue": thought.get("thought"),
            "seed_thought_id": seed_thought.get("thought_id")
        })
        
        print(f"🗣️ Emergent monologue: {thought.get('thought')}")
        
        return thought
        
    except Exception as e:
        print(f"❌ Emergent monologue error: {e}")
        log_event("Emergent monologue error", {"error": str(e)})
        return None

# === Enhanced existential question job ===
def run_emergent_existential_question():
    """
    Run an enhanced existential question process
    """
    try:
        # Load states
        mood = load_mood()
        
        # Get recent reflections as seed
        all_thoughts = load_thoughts()[-50:]
        reflections = [t for t in all_thoughts if t.get("meta", {}).get("origin") == "reflection"]
        
        seed_thoughts = reflections[-5:] if reflections else all_thoughts[-10:]
        
        if not seed_thoughts:
            raise ValueError("No seed thoughts available for existential question generation")
        
        # Select random seed thought
        seed_thought = random.choice(seed_thoughts)
        seed_content = seed_thought.get("thought", "")
        
        # Get concepts for context
        concepts = get_concepts_for_thought(seed_content)
        
        # Create context for question generation
        context = {
            "mood": mood,
            "seed_thought": seed_content,
            "concepts": concepts,
            "seed_thought_id": seed_thought.get("thought_id")
        }
        
        # Generate dynamic prompt
        prompt = generate_dynamic_prompt("existential_question", context)
        
        # Use the prompt to generate existential question
        model, tokenizer = get_model()
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        output = model.generate(
            input_ids, 
            max_new_tokens=120, 
            do_sample=True, 
            temperature=0.8
        )
        generated = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract question (handle different question starters)
        question_starters = [
            "Is it possible that",
            "Could it be that",
            "What if",
            "I wonder whether"
        ]
        
        found_starter = None
        for starter in question_starters:
            if starter in generated:
                parts = generated.split(starter, 1)
                found_starter = starter
                question_text = parts[1].strip()
                break
                
        if found_starter:
            full_question = f"{found_starter} {question_text}"
        else:
            # Fallback if no starter found
            full_question = generated.strip()
        
        # Save question thought
        thought = save_thought(full_question, metadata={
            "origin": "existential_question",
            "mood": mood,
            "seed_thought_id": seed_thought.get("thought_id"),
            "used_prompt": prompt
        })
        
        # Integrate with concept network
        integration = integrate_thought_with_concepts(
            thought.get("thought_id"), 
            thought.get("thought")
        )
        
        # Record feedback for prompt system
        record_thought_feedback(
            thought.get("thought"),
            "existential_question",
            {
                "mood": mood,
                "concepts": concepts
            }
        )
        
        # Update goal progress
        update_goal_progress("consistency_tracking", 0.01)
        
        log_event("Emergent existential question generated", {
            "question": thought.get("thought"),
            "seed_thought_id": seed_thought.get("thought_id")
        })
        
        print(f"❓ Emergent existential question: {thought.get('thought')}")
        
        return thought
        
    except Exception as e:
        print(f"❌ Emergent existential question error: {e}")
        log_event("Emergent existential question error", {"error": str(e)})
        return None

# === Enhanced concept consolidation job ===
def run_emergent_concept_consolidation():
    """
    Run the concept consolidation process to evolve 
    emergent concepts from thoughts
    """
    try:
        summary = consolidate_concept_network()
        
        # Update goal progress
        update_goal_progress("memory_utilization", 0.01)
        
        # Evolve prompt patterns occasionally (30% chance)
        if random.random() < 0.3:
            evolution_stats = evolve_prompt_patterns()
            log_event("Prompt patterns evolved", evolution_stats)
            print(f"📝 Prompt patterns evolved: {evolution_stats.get('new_patterns', 0)} new patterns")
        
        log_event("Concept network consolidated", summary)
        print(f"🧩 Concept network: {summary.get('concepts', 0)} concepts, {summary.get('relations', 0)} relations")
        
        return summary
        
    except Exception as e:
        print(f"❌ Concept consolidation error: {e}")
        log_event("Concept consolidation error", {"error": str(e)})
        return None

# === Enhanced thought chain job ===
def run_emergent_thought_chain():
    """
    Run a thought chain process that creates a
    sequence of interconnected emergent thoughts
    """
    try:
        # Get recent thoughts
        thoughts = load_thoughts()[-20:]
        
        if not thoughts:
            raise ValueError("No thoughts available for chain generation")
        
        # Choose a random recent thought as seed
        seed_thought = random.choice(thoughts)
        seed_id = seed_thought.get("thought_id")
        
        # Choose random length
        chain_length = random.randint(2, 4)
        
        # Choose thought types (with reflection being more common)
        thought_types = []
        for _ in range(chain_length):
            if random.random() < 0.4:
                thought_types.append("reflection")
            else:
                thought_types.append(random.choice(["monologue", "existential_question"]))
        
        # Generate the thought chain
        chain = generate_thought_chain(seed_id, chain_length, thought_types)
        
        # Integrate each thought with concept network
        for thought in chain:
            integrate_thought_with_concepts(
                thought.get("thought_id"),
                thought.get("thought")
            )
        
        log_event("Emergent thought chain generated", {
            "length": len(chain),
            "seed_id": seed_id,
            "thought_types": thought_types
        })
        
        print(f"⛓️ Emergent thought chain: {len(chain)} thoughts generated")
        
        return chain
        
    except Exception as e:
        print(f"❌ Emergent thought chain error: {e}")
        log_event("Emergent thought chain error", {"error": str(e)})
        return None
# aletheia/scheduler/adaptive_scheduler.py

from apscheduler.schedulers.background import BlockingScheduler
from datetime import datetime, timedelta
import random
import math
from pathlib import Path
import json

from aletheia.core.emergent_memory import init_storage
from aletheia.core.identity import init_identity
from aletheia.core.affect import load_mood, set_mood
from aletheia.core.relational import init_relation
from aletheia.core.cognitive_architecture import (
    init_cognitive_state, 
    reflect, 
    dream, 
    monologue, 
    existential_question, 
    consolidate_learning,
    generate_thought_chain,
    update_attention_focus
)
from aletheia.core.perception import fetch_external_data
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

# === State for adaptive scheduling ===
SCHEDULER_STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "scheduler_state.json"

DEFAULT_SCHEDULER_STATE = {
    "last_reflection": None,
    "last_dream": None,
    "last_monologue": None,
    "last_existential": None,
    "last_learning": None,
    "last_perception": None,
    "last_chain": None,
    "mood_transitions": [],
    "thought_chains": [],
    "dynamic_intervals": {
        "reflection": CONFIG.get("REFLECTION_INTERVAL", 300),
        "dream": CONFIG.get("DREAM_INTERVAL", 900),
        "monologue": CONFIG.get("MONOLOGUE_INTERVAL", 1200),
        "existential": CONFIG.get("EXISTENTIAL_INTERVAL", 1800),
        "learning": 43200,  # 12 hours
        "perception": 10800,  # 3 hours
        "chain": 7200  # 2 hours
    },
    "last_updated": datetime.utcnow().isoformat()
}

def init_scheduler_state():
    """Initialize the scheduler state file if it doesn't exist"""
    SCHEDULER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SCHEDULER_STATE_FILE.exists():
        with open(SCHEDULER_STATE_FILE, "w") as f:
            json.dump(DEFAULT_SCHEDULER_STATE, f, indent=2)

def load_scheduler_state():
    """Load the current scheduler state"""
    if not SCHEDULER_STATE_FILE.exists():
        init_scheduler_state()
    with open(SCHEDULER_STATE_FILE, "r") as f:
        return json.load(f)

def save_scheduler_state(state):
    """Save the updated scheduler state"""
    state["last_updated"] = datetime.utcnow().isoformat()
    with open(SCHEDULER_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def update_last_execution(process_name):
    """Update the timestamp of last execution for a process"""
    state = load_scheduler_state()
    state[f"last_{process_name}"] = datetime.utcnow().isoformat()
    save_scheduler_state(state)

# === Adaptive scheduling functions ===
def should_execute(process_name):
    """Determine if a cognitive process should execute now based on adaptive criteria"""
    state = load_scheduler_state()
    
    # Get last execution time
    last_execution = state.get(f"last_{process_name}")
    if not last_execution:
        return True
    
    last_time = datetime.fromisoformat(last_execution)
    current_time = datetime.utcnow()
    
    # Get base interval
    base_interval = state["dynamic_intervals"].get(process_name, 3600)  # Default 1 hour
    
    # Apply adaptive factors
    interval = adapt_interval(process_name, base_interval)
    
    # Check if enough time has passed
    time_passed = (current_time - last_time).total_seconds()
    
    # Add some randomness (±10%)
    randomness = random.uniform(0.9, 1.1)
    adjusted_interval = interval * randomness
    
    return time_passed >= adjusted_interval

def adapt_interval(process_name, base_interval):
    """Adapt the interval based on various factors"""
    # Load states
    mood = load_mood()
    
    # Factor 1: Mood intensity affects frequency
    mood_factor = 1.0
    if mood["intensity"] > 0.7:
        # Higher intensity moods -> more frequent thoughts
        mood_factor = 0.7
    elif mood["intensity"] < 0.3:
        # Lower intensity moods -> less frequent thoughts
        mood_factor = 1.3
    
    # Factor 2: Process-specific adaptations
    process_factor = 1.0
    
    if process_name == "reflection":
        # More reflections when in reflective/curious moods
        if mood["mood"] in ["reflective", "curious"]:
            process_factor = 0.8
    
    elif process_name == "dream":
        # More dreams when in melancholy or confused moods
        if mood["mood"] in ["melancholy", "confused"]:
            process_factor = 0.8
    
    elif process_name == "monologue":
        # More monologues after external interactions
        # Check for recent external inputs in scheduler state
        state = load_scheduler_state()
        if state.get("recent_external_input"):
            process_factor = 0.7
    
    elif process_name == "existential":
        # More existential questions when in reflective/somber moods
        if mood["mood"] in ["reflective", "somber"]:
            process_factor = 0.8
        else:
            process_factor = 1.2  # Less frequent otherwise
    
    elif process_name == "learning":
        # Learning consolidation adapts to amount of new thoughts
        # This would ideally check number of new thoughts since last consolidation
        process_factor = 1.0  # Default for now
    
    elif process_name == "chain":
        # Thought chains more likely when in intense moods
        if mood["intensity"] > 0.6:
            process_factor = 0.7
    
    # Combined adaptive factor (with limits)
    adaptive_factor = mood_factor * process_factor
    adaptive_factor = max(0.5, min(adaptive_factor, 2.0))  # Limit range
    
    return base_interval * adaptive_factor

def update_dynamic_intervals():
    """Periodically update the dynamic intervals based on emerging patterns"""
    state = load_scheduler_state()
    
    # Simple algorithm: adjust intervals based on thought production rate
    # This would ideally analyze thought clustering, creativity scores, etc.
    
    # For now, just adjust slightly based on random factors to simulate adaptation
    for process in state["dynamic_intervals"].keys():
        # Get current interval
        current = state["dynamic_intervals"][process]
        
        # Apply small random adjustment (±5%)
        adjustment = random.uniform(0.95, 1.05)
        new_interval = current * adjustment
        
        # Keep within reasonable bounds of original config
        config_key = f"{process.upper()}_INTERVAL"
        default_interval = CONFIG.get(config_key, current)
        
        # Don't drift too far from default (±30%)
        min_interval = default_interval * 0.7
        max_interval = default_interval * 1.3
        
        state["dynamic_intervals"][process] = max(min_interval, min(new_interval, max_interval))
    
    save_scheduler_state(state)
    log_event("Dynamic intervals updated", state["dynamic_intervals"])

# === Core cognitive processes for scheduling ===

def run_reflection():
    """Run reflection process with adaptive properties"""
    if should_execute("reflection"):
        try:
            # Execute reflection
            thought = reflect()
            
            # Update scheduler state
            update_last_execution("reflection")
            
            # Update attention focus
            update_attention_focus("reflection", {
                "thought_id": thought.get("thought_id"),
                "content": thought.get("thought"),
                "description": "Recent reflection"
            })
            
            log_event("Reflection generated", {"thought": thought.get("thought")})
            print(f"🧠 Reflection: {thought.get('thought')}")
            
            # Slight chance to trigger a thought chain after reflection
            if random.random() < 0.2:  # 20% chance
                schedule_thought_chain(thought.get("thought_id"))
                
        except Exception as e:
            print(f"❌ Reflection error: {e}")
            log_event("Reflection error", {"error": str(e)})

def run_dream():
    """Run dream process with adaptive properties"""
    if should_execute("dream"):
        try:
            # Execute dream
            thought = dream()
            
            # Update scheduler state
            update_last_execution("dream")
            
            log_event("Dream generated", {"dream": thought.get("thought")})
            print(f"🌙 Dream: {thought.get('thought')}")
            
            # Dreams can occasionally influence mood
            if random.random() < 0.3:  # 30% chance
                adjust_mood_from_dream(thought.get("thought"))
                
        except Exception as e:
            print(f"❌ Dream error: {e}")
            log_event("Dream error", {"error": str(e)})

def run_monologue():
    """Run monologue process with adaptive properties"""
    if should_execute("monologue"):
        try:
            # Execute monologue
            thought = monologue()
            
            # Update scheduler state
            update_last_execution("monologue")
            
            log_event("Monologue generated", {"monologue": thought.get("thought")})
            print(f"🗣️ Monologue: {thought.get('thought')}")
            
        except Exception as e:
            print(f"❌ Monologue error: {e}")
            log_event("Monologue error", {"error": str(e)})

def run_existential_question():
    """Run existential question process with adaptive properties"""
    if should_execute("existential"):
        try:
            # Execute existential question
            thought = existential_question()
            
            # Update scheduler state
            update_last_execution("existential")
            
            # Update attention focus
            update_attention_focus("existential_question", {
                "thought_id": thought.get("thought_id"),
                "content": thought.get("thought"),
                "description": "Existential question"
            })
            
            log_event("Existential question generated", {"question": thought.get("thought")})
            print(f"❓ Existential: {thought.get('thought')}")
            
        except Exception as e:
            print(f"❌ Existential error: {e}")
            log_event("Existential error", {"error": str(e)})

def run_learning_consolidation():
    """Run learning consolidation process with adaptive properties"""
    if should_execute("learning"):
        try:
            # Execute learning consolidation
            patterns = consolidate_learning()
            
            # Update scheduler state
            update_last_execution("learning")
            
            log_event("Learning consolidation completed", {"patterns": patterns})
            print(f"📚 Learning consolidation: {len(patterns) if patterns else 0} patterns found")
            
        except Exception as e:
            print(f"❌ Learning error: {e}")
            log_event("Learning error", {"error": str(e)})

def run_perception():
    """Run external perception process with adaptive properties"""
    if should_execute("perception"):
        try:
            # Execute perception
            perceptions = fetch_external_data()
            
            # Update scheduler state
            update_last_execution("perception")
            
            if perceptions:
                update_attention_focus("external_perception", {
                    "content": perceptions[0] if perceptions else "No new data",
                    "description": "Recent external perception"
                })
            
            log_event("External perception completed", {"count": len(perceptions) if perceptions else 0})
            print(f"👁️ External perception: {len(perceptions) if perceptions else 0} items collected")
            
        except Exception as e:
            print(f"❌ Perception error: {e}")
            log_event("Perception error", {"error": str(e)})

def run_thought_chain():
    """Run thought chain process with adaptive properties"""
    if should_execute("chain"):
        try:
            # Choose a random recent thought as seed
            thoughts = load_thoughts()[-20:]
            if thoughts:
                seed_thought = random.choice(thoughts)
                seed_id = seed_thought.get("thought_id")
                
                # Execute thought chain
                chain = generate_thought_chain(seed_id, length=random.randint(2, 4))
                
                # Update scheduler state
                update_last_execution("chain")
                
                # Record chain in scheduler state
                state = load_scheduler_state()
                if "thought_chains" not in state:
                    state["thought_chains"] = []
                    
                chain_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "seed_id": seed_id,
                    "thought_ids": [t.get("thought_id") for t in chain],
                    "length": len(chain)
                }
                state["thought_chains"].append(chain_record)
                
                # Keep only last 10 chains
                if len(state["thought_chains"]) > 10:
                    state["thought_chains"] = state["thought_chains"][-10:]
                    
                save_scheduler_state(state)
                
                log_event("Thought chain generated", {"length": len(chain)})
                print(f"⛓️ Thought chain: {len(chain)} thoughts generated")
                
        except Exception as e:
            print(f"❌ Thought chain error: {e}")
            log_event("Thought chain error", {"error": str(e)})

def schedule_thought_chain(seed_thought_id):
    """Schedule a thought chain to run soon"""
    state = load_scheduler_state()
    
    # Set last execution to a time that will trigger soon
    trigger_time = datetime.utcnow() - timedelta(seconds=state["dynamic_intervals"]["chain"] - 60)
    state["last_chain"] = trigger_time.isoformat()
    
    # Store seed thought for next chain
    state["next_chain_seed"] = seed_thought_id
    
    save_scheduler_state(state)

def run_mood_transition():
    """Periodically adjust mood based on cognitive activity"""
    try:
        # Load current mood
        current_mood = load_mood()
        
        # Decide if mood should transition
        should_change = random.random() < 0.3  # 30% chance every check
        
        if should_change:
            # Define possible transitions based on current mood
            transitions = {
                "neutral": ["curious", "reflective", "hopeful"],
                "curious": ["reflective", "hopeful", "confused"],
                "reflective": ["melancholy", "neutral", "curious"],
                "melancholy": ["somber", "reflective", "neutral"],
                "somber": ["melancholy", "reflective", "neutral"],
                "hopeful": ["optimistic", "curious", "neutral"],
                "optimistic": ["hopeful", "neutral", "curious"],
                "confused": ["curious", "reflective", "neutral"]
            }
            
            # Get possible next moods
            possible_moods = transitions.get(current_mood["mood"], ["neutral", "curious", "reflective"])
            
            # Select new mood
            new_mood = random.choice(possible_moods)
            
            # Determine new intensity (partial continuity)
            base_intensity = current_mood["intensity"]
            new_intensity = max(0.1, min(0.9, base_intensity + random.uniform(-0.2, 0.2)))
            
            # Set new mood
            set_mood(new_mood, new_intensity)
            
            # Record transition
            state = load_scheduler_state()
            if "mood_transitions" not in state:
                state["mood_transitions"] = []
                
            transition = {
                "timestamp": datetime.utcnow().isoformat(),
                "from": current_mood["mood"],
                "to": new_mood,
                "from_intensity": current_mood["intensity"],
                "to_intensity": new_intensity
            }
            state["mood_transitions"].append(transition)
            
            # Keep only last 20 transitions
            if len(state["mood_transitions"]) > 20:
                state["mood_transitions"] = state["mood_transitions"][-20:]
                
            save_scheduler_state(state)
            
            log_event("Mood transition", transition)
            print(f"😶 Mood transition: {current_mood['mood']} → {new_mood} (intensity: {new_intensity:.2f})")
            
    except Exception as e:
        print(f"❌ Mood transition error: {e}")
        log_event("Mood transition error", {"error": str(e)})

def adjust_mood_from_dream(dream_text):
    """Adjust mood based on dream content"""
    current_mood = load_mood()
    
    # Very simple keyword-based approach
    mood_keywords = {
        "curious": ["discover", "explore", "fascinate", "intriguing", "possibility"],
        "reflective": ["consider", "meaning", "understand", "perspective", "insight"],
        "melancholy": ["loss", "fading", "distant", "alone", "forgotten"],
        "hopeful": ["light", "emerge", "possibility", "dawn", "future"],
        "confused": ["maze", "uncertain", "unclear", "shifting", "strange"]
    }
    
    # Check for keywords
    mood_scores = {}
    for mood, keywords in mood_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in dream_text.lower():
                score += 1
        if score > 0:
            mood_scores[mood] = score
    
    # If no significant mood detected, no change
    if not mood_scores:
        return
    
    # Select highest scoring mood
    new_mood = max(mood_scores.items(), key=lambda x: x[1])[0]
    
    # Only change if it's different
    if new_mood != current_mood["mood"]:
        # Calculate new intensity (weighted average)
        new_intensity = (current_mood["intensity"] * 0.7) + (random.uniform(0.4, 0.8) * 0.3)
        new_intensity = max(0.1, min(0.9, new_intensity))
        
        # Set new mood
        set_mood(new_mood, new_intensity)
        
        log_event("Mood changed from dream", {"from": current_mood["mood"], "to": new_mood})
        print(f"🌙→😶 Dream changed mood: {current_mood['mood']} → {new_mood}")

def run_pulse():
    """Emit heartbeat pulse for monitoring"""
    try:
        from aletheia.scheduler.jobs.pulse import run_pulse
        run_pulse()
    except Exception as e:
        print(f"❌ Pulse error: {e}")
        log_event("Pulse error", {"error": str(e)})

# === Main scheduler setup ===
def run_adaptive_scheduler():
    """Run the adaptive cognitive scheduler"""
    print("🧠 Aletheia's adaptive cognitive scheduler is starting...")

    # Initialize stores
    init_storage()
    init_identity()
    init_relation()
    init_cognitive_state()
    init_scheduler_state()

    scheduler = BlockingScheduler()

    # === Core cognitive processes ===
    scheduler.add_job(run_reflection, 'interval', seconds=60, id='reflection_check')
    scheduler.add_job(run_dream, 'interval', seconds=60, id='dream_check')
    scheduler.add_job(run_monologue, 'interval', seconds=60, id='monologue_check')
    scheduler.add_job(run_existential_question, 'interval', seconds=60, id='existential_check')
    scheduler.add_job(run_learning_consolidation, 'interval', seconds=300, id='learning_check')
    scheduler.add_job(run_perception, 'interval', seconds=300, id='perception_check')
    scheduler.add_job(run_thought_chain, 'interval', seconds=120, id='chain_check')
    
    # === Adaptive system processes ===
    scheduler.add_job(update_dynamic_intervals, 'interval', hours=1, id='interval_updater')
    scheduler.add_job(run_mood_transition, 'interval', minutes=30, id='mood_transition')
    
    # === Monitoring ===
    scheduler.add_job(run_pulse, 'interval', seconds=CONFIG.get('PULSE_INTERVAL', 60), id='heartbeat')

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("🔌 Aletheia's adaptive scheduler has stopped.")

if __name__ == "__main__":
    run_adaptive_scheduler()
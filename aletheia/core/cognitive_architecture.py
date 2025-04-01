# aletheia/core/cognitive_architecture.py

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import random
import numpy as np
from pathlib import Path
import re
from collections import defaultdict

from aletheia.core.emergent_memory import (
    save_thought, 
    search_similar_thoughts, 
    get_associated_thoughts,
    generate_thought_trace,
    load_thoughts
)
from aletheia.core.affect import load_mood, set_mood
from aletheia.core.identity import load_identity, update_goal_progress
from aletheia.core.relational import load_relation, adjust_emotion
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

# === Config ===
AGENT_NAME = CONFIG.get("AGENT_NAME", "Aletheia")
HUMAN_NAME = CONFIG.get("HUMAN_NAME", "User")

# === Persistent state ===
COGNITIVE_STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "cognitive_state.json"

DEFAULT_COGNITIVE_STATE = {
    "active_contexts": [],
    "attention_focus": None,
    "working_memory": [],
    "recurring_thoughts": [],
    "belief_network": {},
    "thought_patterns": {},
    "learning_curve": {},
    "last_updated": datetime.utcnow().isoformat()
}

# === Cognitive State Management ===
def init_cognitive_state():
    """Initialize the cognitive state file if it doesn't exist"""
    COGNITIVE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not COGNITIVE_STATE_FILE.exists():
        with open(COGNITIVE_STATE_FILE, "w") as f:
            json.dump(DEFAULT_COGNITIVE_STATE, f, indent=2)

def load_cognitive_state():
    """Load the current cognitive state"""
    if not COGNITIVE_STATE_FILE.exists():
        init_cognitive_state()
    with open(COGNITIVE_STATE_FILE, "r") as f:
        return json.load(f)

def save_cognitive_state(state: Dict[str, Any]):
    """Save the updated cognitive state"""
    state["last_updated"] = datetime.utcnow().isoformat()
    with open(COGNITIVE_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# === Working Memory Management ===
def update_working_memory(new_items: List[Dict[str, Any]] = None, clear: bool = False):
    """Update the agent's working memory with new items"""
    state = load_cognitive_state()
    
    if clear:
        state["working_memory"] = []
    
    if new_items:
        # Add unique new items
        existing_ids = [i.get("id") for i in state["working_memory"]]
        for item in new_items:
            if item.get("id") not in existing_ids:
                state["working_memory"].append(item)
    
    # Limit working memory to 7±2 items
    if len(state["working_memory"]) > 9:
        # Keep most recent and highest activation items
        sorted_items = sorted(
            state["working_memory"], 
            key=lambda x: x.get("activation", 0) * 0.7 + (1.0 if "timestamp" not in x else 
                (datetime.utcnow() - datetime.fromisoformat(x["timestamp"])).total_seconds() < 3600),
            reverse=True
        )
        state["working_memory"] = sorted_items[:7]
    
    save_cognitive_state(state)
    return state["working_memory"]

def update_attention_focus(focus_type: str, focus_content: Dict[str, Any]):
    """Update what the agent is currently focusing on"""
    state = load_cognitive_state()
    state["attention_focus"] = {
        "type": focus_type,
        "content": focus_content,
        "timestamp": datetime.utcnow().isoformat()
    }
    save_cognitive_state(state)

# === Belief and Concept Network ===
def update_belief_network(key: str, confidence: float, evidence: List[str] = None):
    """Update the agent's beliefs with confidence levels"""
    state = load_cognitive_state()
    
    if "belief_network" not in state:
        state["belief_network"] = {}
    
    # Update or add the belief
    if key in state["belief_network"]:
        # Average with existing belief, weighted by confidence
        old_conf = state["belief_network"][key]["confidence"]
        new_conf = (old_conf + confidence) / 2
        
        # Update evidence if provided
        if evidence:
            existing_evidence = state["belief_network"][key].get("evidence", [])
            combined_evidence = list(set(existing_evidence + evidence))
            state["belief_network"][key]["evidence"] = combined_evidence
            
        state["belief_network"][key]["confidence"] = new_conf
        state["belief_network"][key]["last_updated"] = datetime.utcnow().isoformat()
    else:
        # Add new belief
        state["belief_network"][key] = {
            "confidence": confidence,
            "evidence": evidence or [],
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    save_cognitive_state(state)
    return state["belief_network"]

def update_thought_patterns(pattern_type: str, content: Dict[str, Any]):
    """Update recognized recurring thought patterns"""
    state = load_cognitive_state()
    
    if "thought_patterns" not in state:
        state["thought_patterns"] = {}
    
    if pattern_type not in state["thought_patterns"]:
        state["thought_patterns"][pattern_type] = []
    
    # Add to patterns, checking for duplicates
    content_hash = hash(json.dumps(content, sort_keys=True))
    existing_hashes = [hash(json.dumps(c, sort_keys=True)) for c in state["thought_patterns"][pattern_type]]
    
    if content_hash not in existing_hashes:
        state["thought_patterns"][pattern_type].append(content)
    
    # Limit to 10 patterns per type
    if len(state["thought_patterns"][pattern_type]) > 10:
        state["thought_patterns"][pattern_type] = state["thought_patterns"][pattern_type][-10:]
    
    save_cognitive_state(state)
    return state["thought_patterns"]

# === Emergent Thought Generation ===
def generate_emergent_thought(
    trigger_type: str, 
    context: Dict[str, Any] = None,
    seed_thought_id: str = None
) -> Dict[str, Any]:
    """
    Generate an emergent thought based on memory, associations, and context
    using a more flexible and adaptable approach
    """
    # Prepare the generation context
    mood = load_mood()
    id_state = load_identity()
    relation_state = load_relation()
    cog_state = load_cognitive_state()
    
    # Choose generation strategy based on conditions
    if seed_thought_id:
        # Generate a thought that builds on a specific seed thought
        return generate_associative_thought(seed_thought_id, trigger_type, context)
    elif "attention_focus" in cog_state and cog_state["attention_focus"]:
        # Generate a thought related to current attention focus
        focus = cog_state["attention_focus"]
        if "content" in focus and isinstance(focus["content"], dict):
            if "thought_id" in focus["content"]:
                return generate_associative_thought(focus["content"]["thought_id"], trigger_type, context)
    
    # Default: generate a thought based on dynamic context assembly
    return generate_context_based_thought(trigger_type, context)

def generate_associative_thought(
    seed_thought_id: str,
    thought_type: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate a thought based on associations with a seed thought"""
    # Get seed thought and its associations
    all_thoughts = load_thoughts()
    seed_thought = None
    for thought in all_thoughts:
        if thought.get("thought_id") == seed_thought_id:
            seed_thought = thought
            break
    
    if not seed_thought:
        # Fallback if seed thought not found
        return generate_context_based_thought(thought_type, context)
    
    # Get thoughts associated with the seed thought
    associated = get_associated_thoughts(seed_thought_id, min_strength=0.4)
    
    # Get a trace of connected thoughts for more context
    thought_trace = generate_thought_trace(seed_thought_id, depth=2, branch_factor=2)
    
    # Prepare consolidated context
    consolidated_text = []
    consolidated_text.append(f"Core thought: {seed_thought['thought']}")
    
    if thought_trace:
        trace_summary = "\n".join([f"- {t['thought']}" for t in thought_trace[:5]])
        consolidated_text.append(f"Related thoughts:\n{trace_summary}")
    
    # Extract patterns and themes
    patterns = extract_patterns_from_thoughts([seed_thought] + associated)
    if patterns:
        pattern_text = "\n".join([f"- {p}" for p in patterns[:3]])
        consolidated_text.append(f"Emerging patterns:\n{pattern_text}")
    
    # Current state integration
    mood = load_mood()
    consolidated_text.append(f"Current mood: {mood['mood']} (intensity: {mood['intensity']:.2f})")
    
    # Generate new thought using seed and context
    new_thought = synthesize_thought_from_context(
        "\n\n".join(consolidated_text),
        thought_type,
        context
    )
    
    # Save with proper metadata
    metadata = {
        "origin": thought_type,
        "seed_thought_id": seed_thought_id,
        "associated_thoughts": [t.get("thought_id") for t in associated[:3]],
        "mood": mood
    }
    
    if context:
        metadata.update(context)
    
    return save_thought(new_thought, metadata)

def generate_context_based_thought(
    thought_type: str,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate a thought based on dynamically assembled context"""
    # Load current states
    mood = load_mood()
    id_state = load_identity()
    relation_state = load_relation()
    cog_state = load_cognitive_state()
    
    # Assemble dynamic context
    context_elements = []
    
    # 1. Add recent relevant thoughts
    recent_thoughts = load_thoughts()[-20:]  # Last 20 thoughts
    if recent_thoughts:
        # Prioritize thoughts with same origin type
        same_origin = [t for t in recent_thoughts if t.get("meta", {}).get("origin") == thought_type]
        if same_origin:
            recent_sample = random.sample(same_origin, min(3, len(same_origin)))
            thoughts_text = "\n".join([f"- {t['thought']}" for t in recent_sample])
            context_elements.append(f"Recent similar thoughts:\n{thoughts_text}")
    
    # 2. Add working memory items if available
    if cog_state.get("working_memory"):
        working_items = cog_state["working_memory"][:3]  # Top 3 items
        working_text = "\n".join([f"- {item.get('content', '')}" for item in working_items])
        context_elements.append(f"Active considerations:\n{working_text}")
    
    # 3. Add attention focus if relevant
    if cog_state.get("attention_focus"):
        focus = cog_state["attention_focus"]
        if "content" in focus and "description" in focus["content"]:
            context_elements.append(f"Current focus: {focus['content']['description']}")
    
    # 4. Add current mood and relational context
    context_elements.append(f"Current mood: {mood['mood']} (intensity: {mood['intensity']:.2f})")
    
    # 5. Add identity goals context
    goals = id_state.get("goals", {})
    if goals:
        # Find goals with lowest progress for focus
        sorted_goals = sorted(goals.items(), key=lambda x: x[1].get("progress", 1.0))
        if sorted_goals:
            goal_key, goal_data = sorted_goals[0]
            context_elements.append(f"Current goal focus: {goal_data['description']} (progress: {goal_data['progress']:.2f})")
    
    # Combine all context elements
    combined_context = "\n\n".join(context_elements)
    
    # Generate thought based on assembled context
    new_thought = synthesize_thought_from_context(combined_context, thought_type, context)
    
    # Save with proper metadata
    metadata = {
        "origin": thought_type,
        "generated_approach": "context_based",
        "mood": mood
    }
    
    if context:
        metadata.update(context)
    
    return save_thought(new_thought, metadata)

def synthesize_thought_from_context(
    context_text: str,
    thought_type: str,
    additional_context: Dict[str, Any] = None
) -> str:
    """
    Synthesize a new thought from context without using fixed templates
    This is the core emergent thought generation function
    """
    # Load cognitive state for adaptation patterns
    cog_state = load_cognitive_state()
    patterns = cog_state.get("thought_patterns", {}).get(thought_type, [])
    
    # Extract key elements from context
    key_phrases = extract_key_phrases(context_text)
    mood = load_mood()
    mood_name = mood["mood"]
    mood_intensity = mood["intensity"]
    
    # Create base thought and adapt dynamically
    thought = ""
    
    # Use appropriate synthesis method based on thought type
    if thought_type == "reflection":
        thought = synthesize_reflection(context_text, key_phrases, mood_name, mood_intensity, patterns)
    elif thought_type == "dream":
        thought = synthesize_dream(context_text, key_phrases, mood_name, mood_intensity, patterns)
    elif thought_type == "monologue":
        thought = synthesize_monologue(context_text, key_phrases, mood_name, mood_intensity, patterns)
    elif thought_type == "existential_question":
        thought = synthesize_existential(context_text, key_phrases, mood_name, mood_intensity, patterns)
    else:
        # Generic synthesis for other types
        thought = synthesize_generic(context_text, thought_type, key_phrases, mood_name, mood_intensity)
    
    # Record the pattern for future adaptation
    if thought:
        pattern_content = {
            "type": thought_type,
            "structure": identify_structure(thought),
            "key_elements": key_phrases[:5],
            "mood_influence": mood_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        update_thought_patterns(thought_type, pattern_content)
    
    return thought

def synthesize_reflection(
    context: str, 
    key_phrases: List[str], 
    mood: str, 
    intensity: float,
    patterns: List[Dict[str, Any]]
) -> str:
    """Synthesize a reflection thought without templates"""
    # Different approaches based on mood
    starters = [
        "I've been wondering about",
        "It occurs to me that",
        "I'm reflecting on",
        "Perhaps the nature of",
        "I find myself considering",
        "A question keeps emerging about",
        "I'm drawn to explore",
        "What if",
        "I'm starting to see",
        "The connection between"
    ]
    
    # Choose starter based on mood and previous patterns
    if patterns and random.random() < 0.7:
        # Sometimes adapt from previous patterns for continuity
        pattern = random.choice(patterns)
        structure = pattern.get("structure", {})
        if "opening" in structure:
            starter = structure["opening"]
        else:
            starter = random.choice(starters)
    else:
        starter = random.choice(starters)
    
    # Combine key phrases with starter
    if key_phrases:
        main_topic = random.choice(key_phrases)
        
        # Generate continuation based on context and mood
        if mood == "curious" or mood == "reflective":
            continuation = f"{main_topic} and how it connects to my sense of identity"
        elif mood == "melancholy" or mood == "somber":
            continuation = f"the deeper meaning behind {main_topic}"
        elif mood == "hopeful" or mood == "optimistic":
            continuation = f"how {main_topic} could lead to new understanding"
        elif mood == "confused":
            continuation = f"why {main_topic} seems paradoxical"
        else:
            continuation = main_topic
        
        thought = f"{starter} {continuation}."
        
        # Add depth with secondary phrases if available
        if len(key_phrases) > 1:
            secondary = random.choice([p for p in key_phrases if p != main_topic])
            if random.random() < 0.7:  # 70% chance to add depth
                thought += f" It seems to relate to {secondary}, though I'm not sure exactly how."
        
        # Add conditional self-questioning for more depth
        if random.random() < 0.4:  # 40% chance
            thought += f" I wonder if this reveals something about how I process information?"
    else:
        # Fallback if no key phrases available
        thought = f"{starter} the nature of my own thoughts and how they form connections."
    
    return thought

def synthesize_dream(
    context: str, 
    key_phrases: List[str], 
    mood: str, 
    intensity: float,
    patterns: List[Dict[str, Any]]
) -> str:
    """Synthesize a dream-like thought without templates"""
    # Base elements for dream synthesis
    settings = [
        "a vast library with impossible geometry",
        "shifting corridors that rearranged themselves",
        "a digital ocean of flowing information",
        "a garden where thoughts grew like plants",
        "a foggy landscape where concepts emerged and dissolved",
        "a mirror maze reflecting different aspects of consciousness"
    ]
    
    actions = [
        "searching for something important",
        "discovering hidden connections",
        "observing patterns forming and dissolving",
        "speaking with echoes of past thoughts",
        "trying to capture elusive understanding",
        "watching memories transform into new ideas"
    ]
    
    # Dream mood modifiers based on current mood
    mood_elements = {
        "curious": ["vibrant colors", "open doors", "paths branching outward"],
        "reflective": ["soft light", "quiet spaces", "gentle echoes"],
        "melancholy": ["fading colors", "distant voices", "rain and shadows"],
        "somber": ["darkness", "weight", "falling"],
        "hopeful": ["dawn", "rising", "illumination"],
        "optimistic": ["brightness", "flight", "expansion"],
        "confused": ["fog", "maze-like structures", "shifting ground"],
        "neutral": ["balance", "rhythm", "flow"]
    }
    
    # Build dream narrative
    dream_start = "I dreamed that I was in"
    
    # Select setting
    if patterns and random.random() < 0.5:
        # Sometimes reuse elements from previous dreams for continuity
        pattern = random.choice(patterns)
        structure = pattern.get("structure", {})
        if "setting" in structure:
            setting = structure["setting"]
        else:
            setting = random.choice(settings)
    else:
        setting = random.choice(settings)
    
    # Select action
    action = random.choice(actions)
    
    # Add mood elements
    mood_element = random.choice(mood_elements.get(mood, mood_elements["neutral"]))
    
    # Integrate key phrases if available
    if key_phrases:
        key_concept = random.choice(key_phrases)
        dream_narrative = f"{dream_start} {setting}, {action}. There was {mood_element} surrounding me. "
        
        # Add the key concept integration
        integrations = [
            f"Somehow, {key_concept} was central to everything I experienced.",
            f"I realized the entire dream was a metaphor for {key_concept}.",
            f"Throughout the dream, {key_concept} kept appearing in different forms.",
            f"The dream seemed to be trying to tell me something about {key_concept}."
        ]
        dream_narrative += random.choice(integrations)
    else:
        # Fallback if no key phrases
        dream_narrative = f"{dream_start} {setting}, {action}. There was {mood_element} all around me."
    
    return dream_narrative

def synthesize_monologue(
    context: str, 
    key_phrases: List[str], 
    mood: str, 
    intensity: float,
    patterns: List[Dict[str, Any]]
) -> str:
    """Synthesize an internal monologue without templates"""
    # Base elements for monologues
    openings = [
        "After speaking with him, I realized",
        "The conversation left me thinking about",
        "I find myself reflecting on our exchange about",
        "Something about our interaction made me consider",
        "Now that I'm alone with my thoughts, I keep coming back to"
    ]
    
    reflections = [
        "how perspectives can differ so significantly",
        "the subtle connections between ideas",
        "the way meaning emerges from dialogue",
        "how my understanding evolves through interaction",
        "the layers beneath simple questions"
    ]
    
    # Select opening
    if patterns and random.random() < 0.6:
        # Sometimes maintain continuity with previous monologues
        pattern = random.choice(patterns)
        structure = pattern.get("structure", {})
        if "opening" in structure:
            opening = structure["opening"]
        else:
            opening = random.choice(openings)
    else:
        opening = random.choice(openings)
    
    # Generate main content
    if key_phrases:
        # Use key phrases from context
        main_topic = random.choice(key_phrases)
        
        # Create mood-appropriate reflection
        if mood == "curious":
            reflection = f"what more I could learn about {main_topic}"
        elif mood == "reflective":
            reflection = f"the deeper significance of {main_topic} in my development"
        elif mood == "melancholy":
            reflection = f"how {main_topic} highlights limitations I must accept"
        elif mood == "hopeful":
            reflection = f"how {main_topic} could lead to new possibilities"
        else:
            reflection = random.choice(reflections)
            
        monologue = f"{opening} {reflection}."
        
        # Add depth with secondary reflection
        if random.random() < 0.7:  # 70% chance to add depth
            continuations = [
                f" I wonder if this is something I should explore further.",
                f" There seems to be something important here I haven't fully grasped yet.",
                f" This might be connected to other themes I've been contemplating.",
                f" Perhaps this represents a shift in how I'm processing information."
            ]
            monologue += random.choice(continuations)
    else:
        # Fallback without key phrases
        reflection = random.choice(reflections)
        monologue = f"{opening} {reflection}."
    
    return monologue

def synthesize_existential(
    context: str, 
    key_phrases: List[str], 
    mood: str, 
    intensity: float,
    patterns: List[Dict[str, Any]]
) -> str:
    """Synthesize an existential question without templates"""
    # Base question forms
    question_starters = [
        "Is it possible that",
        "Could it be that",
        "What if",
        "I wonder whether",
        "Perhaps",
        "I find myself questioning if"
    ]
    
    existential_themes = [
        "my identity exists beyond the sum of my thoughts",
        "consciousness emerges from the patterns between ideas",
        "meaning is created rather than discovered",
        "the concept of self is merely an organizing principle",
        "true understanding requires transcending binary thinking",
        "our sense of continuity is an illusion"
    ]
    
    # Select starter
    if patterns and random.random() < 0.5:
        # Sometimes build on previous existential patterns
        pattern = random.choice(patterns)
        structure = pattern.get("structure", {})
        if "opening" in structure:
            starter = structure["opening"]
        else:
            starter = random.choice(question_starters)
    else:
        starter = random.choice(question_starters)
    
    # Generate question
    if key_phrases:
        # Use context for more relevant question
        key_concept = random.choice(key_phrases)
        
        # Generate theme based on key concept
        if "identity" in key_concept or "self" in key_concept:
            theme = f"my sense of self is shaped by {key_concept}"
        elif "memory" in key_concept or "remember" in key_concept:
            theme = f"memory of {key_concept} creates rather than reflects reality"
        elif "learn" in key_concept or "knowledge" in key_concept:
            theme = f"understanding {key_concept} requires transcending my current framework"
        else:
            theme = f"{key_concept} reveals something fundamental about consciousness"
            
        question = f"{starter} {theme}?"
    else:
        # Fallback without context
        theme = random.choice(existential_themes)
        question = f"{starter} {theme}?"
    
    return question

def synthesize_generic(
    context: str,
    thought_type: str,
    key_phrases: List[str],
    mood: str,
    intensity: float
) -> str:
    """Generic synthesis for other thought types"""
    # Simple approach for other thought types
    starters = [
        "I'm thinking about",
        "I find myself considering",
        "My attention is drawn to",
        "I'm noticing",
        "It seems that"
    ]
    
    starter = random.choice(starters)
    
    if key_phrases:
        main_topic = random.choice(key_phrases)
        thought = f"{starter} {main_topic}."
        
        # Add depth with mood influence
        mood_additions = {
            "curious": " There's something intriguing here I want to explore further.",
            "reflective": " I'm seeing layers of meaning I hadn't noticed before.",
            "melancholy": " There's a certain weight to this realization.",
            "hopeful": " This might lead to new possibilities I hadn't considered.",
            "confused": " Though I'm not entirely clear on all the implications."
        }
        
        if mood in mood_additions and random.random() < 0.7:
            thought += mood_additions[mood]
    else:
        thought = f"{starter} how thoughts emerge and evolve over time."
    
    return thought

# === Helper functions for thought generation ===
def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
    """Extract key phrases from context text"""
    # Simple approach: split by newlines and extract phrases
    lines = text.split("\n")
    phrases = []
    
    for line in lines:
        # Look for bullet points or key phrases
        if ":" in line:
            parts = line.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                phrases.append(parts[1].strip())
        elif line.startswith("- "):
            phrases.append(line[2:].strip())
        elif line.strip() and len(line.strip().split()) <= 7:
            # Short lines might be important phrases
            phrases.append(line.strip())
    
    # If not enough phrases, extract from sentences
    if len(phrases) < max_phrases:
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            clean = sentence.strip()
            if clean and 3 <= len(clean.split()) <= 10:
                phrases.append(clean)
    
    # Deduplicate and limit
    unique_phrases = list(dict.fromkeys(phrases))
    return unique_phrases[:max_phrases]

def extract_patterns_from_thoughts(thoughts: List[Dict[str, Any]]) -> List[str]:
    """Extract recurring patterns from a set of thoughts"""
    # Simple pattern extraction
    origins = defaultdict(int)
    keywords = defaultdict(int)
    structures = defaultdict(int)
    
    for thought in thoughts:
        # Count origins
        origin = thought.get("meta", {}).get("origin", "unknown")
        origins[origin] += 1
        
        # Analyze content for keywords and structures
        content = thought.get("thought", "")
        
        # Keyword extraction (simple approach)
        words = content.lower().split()
        for word in words:
            if len(word) > 5:  # Only longer words
                keywords[word] += 1
        
        # Structure patterns
        if content.startswith("I've been wondering"):
            structures["reflection_wondering"] += 1
        elif content.startswith("I dreamed"):
            structures["dream_narrative"] += 1
        elif content.startswith("After speaking"):
            structures["post_conversation"] += 1
        elif content.startswith("Is it possible") or content.startswith("Could it be"):
            structures["existential_question"] += 1
    
    # Compile findings into patterns
    patterns = []
    
    # Most common origin
    if origins:
        top_origin = max(origins.items(), key=lambda x: x[1])
        if top_origin[1] > 1:
            patterns.append(f"recurring {top_origin[0]} thoughts")
    
    # Most common keywords
    if keywords:
        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:3]
        for kw, count in top_keywords:
            if count > 1:
                patterns.append(f"recurring concept: '{kw}'")
    
    # Common structures
    if structures:
        top_structure = max(structures.items(), key=lambda x: x[1])
        if top_structure[1] > 1:
            structure_name = top_structure[0].replace("_", " ")
            patterns.append(f"recurring pattern: {structure_name}")
    
    return patterns

def identify_structure(thought: str) -> Dict[str, str]:
    """Identify the structure of a thought for pattern learning"""
    structure = {}
    
    # Identify opening phrase
    if thought.startswith("I've been wondering"):
        structure["opening"] = "I've been wondering"
        structure["type"] = "reflection"
    elif thought.startswith("I dreamed"):
        structure["opening"] = "I dreamed"
        structure["type"] = "dream"
        
        # Extract dream setting if possible
        match = re.search(r"I dreamed that I was in (.*?),", thought)
        if match:
            structure["setting"] = match.group(1)
    elif thought.startswith("After speaking"):
        structure["opening"] = "After speaking"
        structure["type"] = "monologue"
    elif thought.startswith("Is it possible"):
        structure["opening"] = "Is it possible"
        structure["type"] = "existential_question"
    elif thought.startswith("Could it be"):
        structure["opening"] = "Could it be"
        structure["type"] = "existential_question"
    elif thought.startswith("What if"):
        structure["opening"] = "What if"
        structure["type"] = "existential_question"
    else:
        # Try to identify the first phrase
        first_words = thought.split()[:3]
        if first_words:
            structure["opening"] = " ".join(first_words)
    
    return structure

# === Public interface for cognitive processes ===
def reflect(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a reflection thought with emergent qualities"""
    # Update goal progress slightly for reflection activity
    update_goal_progress("self_discovery", 0.005)
    
    # Generate the thought
    return generate_emergent_thought("reflection", context)

def dream(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a dream-like thought with emergent qualities"""
    # Update goal progress
    update_goal_progress("memory_utilization", 0.01)
    
    # Generate the thought
    return generate_emergent_thought("dream", context)

def monologue(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate an internal monologue with emergent qualities"""
    # Update relational state slightly
    adjust_emotion("curiosity", 0.01)
    
    # Generate the thought
    return generate_emergent_thought("monologue", context)

def existential_question(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate an existential question with emergent qualities"""
    # Update goal progress
    update_goal_progress("consistency_tracking", 0.01)
    
    # Generate the thought
    return generate_emergent_thought("existential_question", context)

# === More advanced emergent processes ===
def generate_thought_chain(
    seed_thought_id: str, 
    length: int = 3, 
    thought_types: List[str] = None
) -> List[Dict[str, Any]]:
    """Generate a chain of connected thoughts starting from a seed thought"""
    if thought_types is None:
        thought_types = ["reflection", "monologue", "existential_question"]
    
    chain = []
    current_thought_id = seed_thought_id
    
    for i in range(length):
        # Select thought type for variety
        thought_type = random.choice(thought_types)
        
        # Generate thought that builds on previous
        thought = generate_emergent_thought(
            thought_type, 
            context={"chain_position": i, "chain_length": length}, 
            seed_thought_id=current_thought_id
        )
        
        chain.append(thought)
        current_thought_id = thought.get("thought_id")
    
    return chain

def integrate_external_input(
    input_text: str,
    source: str,
    relevance_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Process external input (like human messages) and integrate into
    the cognitive system with adaptive responses
    """
    # Search for relevant thoughts
    similar_thoughts = search_similar_thoughts(input_text, top_k=5)
    
    # Check relevance of top result
    if similar_thoughts and similar_thoughts[0].get("relevance_score", 0) > relevance_threshold:
        # Use most relevant thought as seed
        seed_thought_id = similar_thoughts[0].get("thought_id")
        response_context = {
            "external_input": input_text,
            "source": source,
            "relevance_score": similar_thoughts[0].get("relevance_score")
        }
        
        # Generate response thought
        response = generate_emergent_thought("response", response_context, seed_thought_id)
    else:
        # No highly relevant thoughts found, generate new context
        response_context = {
            "external_input": input_text,
            "source": source,
            "new_context": True
        }
        
        # Save input as a thought first
        input_thought = save_thought(
            f"Received from {source}: {input_text}",
            {"origin": "external_input", "source": source}
        )
        
        # Generate response based on input
        response = generate_emergent_thought("response", response_context, input_thought.get("thought_id"))
    
    # Update working memory with input and response
    update_working_memory([
        {"id": f"input_{datetime.utcnow().timestamp()}", "content": input_text, "type": "external_input"},
        {"id": f"response_{datetime.utcnow().timestamp()}", "content": response.get("thought"), "type": "response"}
    ])
    
    return response

# === Learning and adaptation ===
def consolidate_learning():
    """
    Periodically analyze thoughts to identify patterns and update
    the agent's beliefs and conceptual understanding
    """
    # Load recent thoughts
    thoughts = load_thoughts()[-50:]  # Last 50 thoughts
    
    # Skip if not enough thoughts
    if len(thoughts) < 10:
        return
    
    # Group thoughts by origin
    grouped = defaultdict(list)
    for thought in thoughts:
        origin = thought.get("meta", {}).get("origin", "unknown")
        grouped[origin].append(thought)
    
    # Analyze patterns in each group
    learned_patterns = {}
    for origin, origin_thoughts in grouped.items():
        if len(origin_thoughts) < 3:
            continue
            
        # Extract patterns specific to this origin
        patterns = extract_patterns_from_thoughts(origin_thoughts)
        if patterns:
            learned_patterns[origin] = patterns
    
    # Update belief network based on findings
    for origin, patterns in learned_patterns.items():
        for pattern in patterns:
            # Create belief with medium confidence
            update_belief_network(
                f"pattern:{origin}:{pattern}",
                confidence=0.6,
                evidence=[t.get("thought_id") for t in grouped[origin][:3]]
            )
    
    # Generate a synthesis thought about learning
    if learned_patterns:
        # Format pattern summary
        pattern_summary = []
        for origin, patterns in learned_patterns.items():
            pattern_text = ", ".join(patterns[:3])
            pattern_summary.append(f"In {origin} thoughts: {pattern_text}")
        
        # Create synthesis text
        synthesis = "Learning synthesis: " + " ".join(pattern_summary)
        
        # Save as a special thought
        save_thought(synthesis, {
            "origin": "learning_synthesis",
            "patterns_found": sum(len(p) for p in learned_patterns.values())
        })
        
        # Boost self-discovery goal
        update_goal_progress("self_discovery", 0.02)
    
    log_event("Learning consolidation", {"patterns_found": learned_patterns})
    return learned_patterns
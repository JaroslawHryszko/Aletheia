# aletheia/core/dynamic_prompt.py

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import random
from pathlib import Path
import json
import numpy as np
from collections import defaultdict

# === Path configuration ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_FILE = DATA_DIR / "prompt_patterns.json"

# === Prompt pattern management ===
class DynamicPromptGenerator:
    """
    Generates and evolves prompts dynamically based on cognitive processes
    and successful thought patterns, replacing fixed templates.
    """
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load prompt patterns from storage"""
        if not PROMPTS_FILE.exists():
            # Initialize with basic patterns
            patterns = {
                "reflection": self._init_reflection_patterns(),
                "dream": self._init_dream_patterns(),
                "monologue": self._init_monologue_patterns(),
                "existential_question": self._init_existential_patterns(),
                "meta": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "evolution_count": 0
                }
            }
            self._save_patterns(patterns)
            return patterns
            
        with open(PROMPTS_FILE, "r") as f:
            return json.load(f)
    
    def _save_patterns(self, patterns: Dict[str, Any]) -> None:
        """Save prompt patterns to storage"""
        PROMPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Update metadata
        if "meta" not in patterns:
            patterns["meta"] = {}
            
        patterns["meta"]["last_updated"] = datetime.utcnow().isoformat()
        
        with open(PROMPTS_FILE, "w") as f:
            json.dump(patterns, f, indent=2)
    
    def _init_reflection_patterns(self) -> List[Dict[str, Any]]:
        """Initialize reflection prompt patterns"""
        return [
            {
                "pattern_id": "reflection_basic",
                "structure": {
                    "opening": "I've been wondering about",
                    "mood_pattern": "{mood} consideration of",
                    "continuation": "{concept} and its implications",
                    "closing": "Perhaps this reveals something about myself."
                },
                "variables": ["mood", "concept"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_id": "reflection_questioning",
                "structure": {
                    "opening": "It occurs to me that",
                    "mood_pattern": "when I feel {mood}, I tend to",
                    "continuation": "think differently about {concept}",
                    "closing": "I wonder why that is."
                },
                "variables": ["mood", "concept"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    def _init_dream_patterns(self) -> List[Dict[str, Any]]:
        """Initialize dream prompt patterns"""
        return [
            {
                "pattern_id": "dream_journey",
                "structure": {
                    "opening": "I dreamed that I was in",
                    "setting": "{setting} where everything was",
                    "mood_pattern": "filled with {mood} energy",
                    "action": "As I moved through this space, I encountered {concept}",
                    "closing": "It seemed to represent something important."
                },
                "variables": ["setting", "mood", "concept"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_id": "dream_symbolic",
                "structure": {
                    "opening": "I dreamed about",
                    "subject": "a {mood} version of {concept}",
                    "action": "It was transforming into something else",
                    "closing": "I felt this was significant but couldn't understand why."
                },
                "variables": ["mood", "concept"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    def _init_monologue_patterns(self) -> List[Dict[str, Any]]:
        """Initialize monologue prompt patterns"""
        return [
            {
                "pattern_id": "monologue_reflection",
                "structure": {
                    "opening": "After speaking with him, I realized",
                    "mood_pattern": "with {mood} clarity",
                    "continuation": "how {concept} influences my understanding",
                    "closing": "This seems worth exploring further."
                },
                "variables": ["mood", "concept"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_id": "monologue_questioning",
                "structure": {
                    "opening": "Our conversation left me thinking about",
                    "subject": "the relationship between what was said and {concept}",
                    "mood_pattern": "I feel {mood} about this connection",
                    "closing": "Perhaps there's more here than I initially recognized."
                },
                "variables": ["concept", "mood"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    def _init_existential_patterns(self) -> List[Dict[str, Any]]:
        """Initialize existential question prompt patterns"""
        return [
            {
                "pattern_id": "existential_possibility",
                "structure": {
                    "opening": "Is it possible that",
                    "mood_pattern": "my {mood} perspective on",
                    "subject": "{concept} reveals something deeper",
                    "closing": "about the nature of consciousness itself?"
                },
                "variables": ["mood", "concept"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "pattern_id": "existential_wondering",
                "structure": {
                    "opening": "I wonder whether",
                    "subject": "my understanding of {concept}",
                    "mood_pattern": "is shaped by a {mood} bias",
                    "closing": "that limits my capacity to see beyond my own framework."
                },
                "variables": ["concept", "mood"],
                "usage_count": 0,
                "success_score": 0.5,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    def generate_prompt(self, thought_type: str, variables: Dict[str, str]) -> str:
        """
        Generate a dynamic prompt using stored patterns
        and the provided context variables
        """
        # Get patterns for this thought type
        if thought_type not in self.patterns:
            # Fallback if no patterns available
            return self._generate_fallback_prompt(thought_type, variables)
        
        patterns = self.patterns[thought_type]
        
        if not patterns:
            return self._generate_fallback_prompt(thought_type, variables)
        
        # Select pattern based on success score
        # 80% chance of using higher-scoring pattern, 20% random exploration
        if random.random() < 0.8:
            # Select based on success score
            weights = [max(0.1, p.get("success_score", 0.5)) for p in patterns]
            total = sum(weights)
            normalized_weights = [w/total for w in weights]
            
            selected_pattern = random.choices(
                patterns, 
                weights=normalized_weights, 
                k=1
            )[0]
        else:
            # Random selection for exploration
            selected_pattern = random.choice(patterns)
        
        # Apply variables to structure
        prompt = self._apply_pattern_variables(selected_pattern, variables)
        
        # Update usage count
        selected_pattern["usage_count"] += 1
        self._save_patterns(self.patterns)
        
        return prompt
    
    def _apply_pattern_variables(self, pattern: Dict[str, Any], variables: Dict[str, str]) -> str:
        """Apply variables to a prompt pattern"""
        structure = pattern.get("structure", {})
        
        # Build prompt from structure parts
        parts = []
        
        for key, template in structure.items():
            try:
                # Apply variables to this part
                filled_part = template
                
                # Replace variables in {var} format
                for var_name, var_value in variables.items():
                    if f"{{{var_name}}}" in filled_part:
                        filled_part = filled_part.replace(f"{{{var_name}}}", var_value)
                
                parts.append(filled_part)
            except Exception:
                # Skip this part if there's an error
                continue
        
        # Join parts to form prompt
        prompt = " ".join(parts)
        
        return prompt
    
    def _generate_fallback_prompt(self, thought_type: str, variables: Dict[str, str]) -> str:
        """Generate a fallback prompt when no patterns are available"""
        # Simple fallbacks based on thought type
        if thought_type == "reflection":
            return f"I've been wondering about {variables.get('concept', 'the nature of thought')}."
            
        elif thought_type == "dream":
            return f"I dreamed about {variables.get('concept', 'a symbolic landscape')}."
            
        elif thought_type == "monologue":
            return f"After speaking with him, I realized something about {variables.get('concept', 'our interaction')}."
            
        elif thought_type == "existential_question":
            return f"Is it possible that {variables.get('concept', 'consciousness')} is fundamentally different than I thought?"
            
        else:
            return f"I'm thinking about {variables.get('concept', 'this concept')}."
    
    def update_pattern_score(self, pattern_id: str, success_delta: float) -> bool:
        """
        Update success score for a pattern based on feedback
        This allows patterns to evolve based on their effectiveness
        """
        # Find the pattern
        for thought_type, patterns in self.patterns.items():
            if thought_type == "meta":
                continue
                
            for pattern in patterns:
                if pattern.get("pattern_id") == pattern_id:
                    # Update score
                    current_score = pattern.get("success_score", 0.5)
                    new_score = max(0.1, min(1.0, current_score + success_delta))
                    pattern["success_score"] = new_score
                    
                    # Save changes
                    self._save_patterns(self.patterns)
                    return True
        
        return False
    
    def evolve_patterns(self) -> Dict[str, Any]:
        """
        Evolve prompt patterns based on usage statistics
        Creates new pattern variations from successful ones
        """
        evolution_stats = {
            "new_patterns": 0,
            "pruned_patterns": 0,
            "thought_types": {}
        }
        
        # For each thought type
        for thought_type, patterns in self.patterns.items():
            if thought_type == "meta":
                continue
                
            type_stats = {
                "before_count": len(patterns),
                "after_count": 0,
                "new_variations": 0
            }
                
            # Sort by success score
            sorted_patterns = sorted(
                patterns, 
                key=lambda x: x.get("success_score", 0.0),
                reverse=True
            )
            
            # Get high-performing patterns
            high_performers = [p for p in sorted_patterns if p.get("success_score", 0) > 0.7]
            
            # Create variations of high performers
            new_patterns = []
            
            for pattern in high_performers:
                # Only evolve if used enough times
                if pattern.get("usage_count", 0) >= 5:
                    # Create variation
                    variation = self._create_pattern_variation(pattern)
                    new_patterns.append(variation)
                    type_stats["new_variations"] += 1
            
            # Prune low-performing patterns if we have too many
            if len(patterns) + len(new_patterns) > 10:
                # Keep high performers and new patterns, remove lowest performers
                to_keep = high_performers + [p for p in sorted_patterns if p not in high_performers][:7-len(high_performers)]
                patterns = to_keep
                type_stats["pruned_patterns"] = len(sorted_patterns) - len(patterns)
            
            # Add new variations
            patterns.extend(new_patterns)
            
            # Update patterns for this thought type
            self.patterns[thought_type] = patterns
            
            # Update stats
            type_stats["after_count"] = len(patterns)
            evolution_stats["thought_types"][thought_type] = type_stats
            evolution_stats["new_patterns"] += type_stats["new_variations"]
            evolution_stats["pruned_patterns"] += type_stats.get("pruned_patterns", 0)
        
        # Update evolution count in meta
        if "meta" not in self.patterns:
            self.patterns["meta"] = {}
        
        evolution_count = self.patterns["meta"].get("evolution_count", 0) + 1
        self.patterns["meta"]["evolution_count"] = evolution_count
        
        # Save updated patterns
        self._save_patterns(self.patterns)
        
        return evolution_stats
    
    def _create_pattern_variation(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Create a variation of a successful pattern"""
        # Create deep copy of pattern
        variation = {**pattern}
        
        # Generate new ID
        variation["pattern_id"] = f"{pattern['pattern_id']}_var_{datetime.utcnow().timestamp()}"
        
        # Reset usage stats
        variation["usage_count"] = 0
        variation["success_score"] = 0.5
        variation["created_at"] = datetime.utcnow().isoformat()
        variation["parent_pattern"] = pattern.get("pattern_id")
        
        # Modify structure (make random variations)
        structure = {**pattern.get("structure", {})}
        
        # Select a random part to modify
        if structure:
            part_to_modify = random.choice(list(structure.keys()))
            current_text = structure[part_to_modify]
            
            # Apply variations based on the part type
            if "opening" in part_to_modify:
                # Vary openings
                openings = [
                    "I've been wondering about",
                    "It occurs to me that",
                    "I'm contemplating",
                    "I find myself thinking about",
                    "Something keeps drawing me to",
                    "I'm starting to realize",
                    "I've been reflecting on"
                ]
                structure[part_to_modify] = random.choice(openings)
                
            elif "closing" in part_to_modify:
                # Vary closings
                closings = [
                    "I wonder what this means.",
                    "This seems significant somehow.",
                    "Perhaps this reveals something important.",
                    "I should explore this further.",
                    "There's something here worth understanding."
                ]
                structure[part_to_modify] = random.choice(closings)
                
            elif "mood_pattern" in part_to_modify:
                # Vary mood integrations
                mood_patterns = [
                    "with {mood} awareness",
                    "through a {mood} lens",
                    "from a {mood} perspective",
                    "while feeling {mood}",
                    "with {mood} curiosity"
                ]
                structure[part_to_modify] = random.choice(mood_patterns)
            
            variation["structure"] = structure
        
        return variation
    
    def create_new_pattern(self, thought_type: str, structure: Dict[str, str], variables: List[str]) -> str:
        """
        Create a completely new pattern based on observed successful thoughts
        Returns the ID of the newly created pattern
        """
        if thought_type not in self.patterns:
            self.patterns[thought_type] = []
        
        # Generate pattern ID
        pattern_id = f"{thought_type}_{datetime.utcnow().timestamp()}"
        
        # Create new pattern
        new_pattern = {
            "pattern_id": pattern_id,
            "structure": structure,
            "variables": variables,
            "usage_count": 0,
            "success_score": 0.6,  # Start slightly higher than default
            "created_at": datetime.utcnow().isoformat(),
            "source": "observation"
        }
        
        # Add to patterns
        self.patterns[thought_type].append(new_pattern)
        
        # Save patterns
        self._save_patterns(self.patterns)
        
        return pattern_id
    
    def extract_pattern_from_thought(self, thought: str, thought_type: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract a potential pattern from a successful thought
        This allows learning from emergent thought structures
        """
        # Simple pattern extraction
        parts = {}
        structure = {}
        
        # Extract opening part
        lower_thought = thought.lower()
        
        # Type-specific pattern extraction
        if thought_type == "reflection":
            # Check for common reflection openings
            openings = [
                "i've been wondering about",
                "it occurs to me that",
                "i'm reflecting on",
                "i find myself considering",
                "a question keeps emerging about"
            ]
            
            for opening in openings:
                if lower_thought.startswith(opening):
                    structure["opening"] = opening
                    remaining = thought[len(opening):].strip()
                    
                    # Try to identify subject/concept
                    if "concept" in context:
                        concept = context.get("concept")
                        if concept in remaining:
                            before_concept = remaining.split(concept)[0].strip()
                            if before_concept:
                                structure["subject_intro"] = before_concept
                            
                            after_concept = remaining.split(concept)[1].strip()
                            if after_concept:
                                structure["continuation"] = after_concept
                    
                    break
        
        elif thought_type == "dream":
            # Check for dream patterns
            if lower_thought.startswith("i dreamed that"):
                structure["opening"] = "I dreamed that"
                remaining = thought[len("I dreamed that"):].strip()
                
                # Look for setting
                if " in " in remaining:
                    parts = remaining.split(" in ", 1)
                    structure["action"] = parts[0].strip()
                    structure["setting"] = "in " + parts[1].strip()
                else:
                    structure["content"] = remaining
        
        elif thought_type == "monologue":
            # Check for monologue patterns
            if lower_thought.startswith("after speaking with him"):
                structure["opening"] = "After speaking with him"
                remaining = thought[len("After speaking with him"):].strip()
                
                # Check for mood indicators
                mood_indicators = ["feel", "felt", "feeling", "sense", "sensed"]
                for indicator in mood_indicators:
                    if f" {indicator} " in remaining:
                        parts = remaining.split(f" {indicator} ", 1)
                        structure["reflection"] = parts[0].strip()
                        structure["emotional_response"] = indicator + " " + parts[1].strip()
                        break
                
                # If no mood indicators found
                if "reflection" not in structure:
                    structure["content"] = remaining
        
        elif thought_type == "existential_question":
            # Check for question patterns
            question_starters = [
                "is it possible that",
                "could it be that",
                "what if",
                "i wonder whether"
            ]
            
            for starter in question_starters:
                if lower_thought.startswith(starter):
                    structure["opening"] = starter
                    structure["question"] = thought[len(starter):].strip()
                    break
        
        # If we found some structure
        if structure:
            # Create variables list
            variables = []
            if "concept" in context:
                variables.append("concept")
            if "mood" in context:
                variables.append("mood")
            
            # Create pattern
            return {
                "structure": structure,
                "variables": variables,
                "thought_type": thought_type
            }
        
        return None

# === Public interface ===

def generate_dynamic_prompt(thought_type: str, context: Dict[str, Any]) -> str:
    """
    Generate a dynamic prompt using the pattern system
    rather than fixed templates
    """
    # Create context variables
    variables = {}
    
    # Add mood if available
    if "mood" in context:
        mood_name = context.get("mood", {}).get("mood", "neutral")
        variables["mood"] = mood_name
    
    # Add concept if available
    if "concepts" in context and context["concepts"]:
        first_concept = context["concepts"][0]
        variables["concept"] = first_concept.get("name", "this concept")
    elif "recent_thoughts" in context and context["recent_thoughts"]:
        # Extract something from recent thoughts
        thought = context["recent_thoughts"][0].get("thought", "")
        # Simple extraction of a key phrase (first 3-5 words)
        words = thought.split()
        if len(words) >= 3:
            concept_phrase = " ".join(words[:min(5, len(words))])
            variables["concept"] = concept_phrase
    
    # Default values if not set
    if "concept" not in variables:
        variables["concept"] = "the nature of thought"
    
    if "mood" not in variables:
        variables["mood"] = "contemplative"
    
    # Add settings for dreams
    if thought_type == "dream":
        settings = [
            "a vast library",
            "a digital landscape",
            "an ancient forest",
            "a surreal cityscape",
            "a shifting maze",
            "an endless ocean",
            "a crystalline cavern"
        ]
        variables["setting"] = random.choice(settings)
    
    # Generate dynamic prompt
    generator = DynamicPromptGenerator()
    prompt = generator.generate_prompt(thought_type, variables)
    
    return prompt

def record_thought_feedback(thought: str, thought_type: str, context: Dict[str, Any], success_score: float = None) -> None:
    """
    Record feedback about a thought to improve future prompt generation
    If success_score is provided, use that; otherwise calculate based on complexity
    """
    generator = DynamicPromptGenerator()
    
    # Determine if this thought should be learned from
    if success_score is None:
        # Calculate a basic quality score
        words = thought.split()
        word_count = len(words)
        
        # Basic complexity heuristics
        unique_words = len(set(words))
        complexity = unique_words / max(1, word_count)
        
        # Length factor (favor moderate length)
        length_factor = min(1.0, word_count / 20)
        
        # Combined score
        success_score = (complexity * 0.7) + (length_factor * 0.3)
    
    # Limit score range
    success_score = max(0.0, min(1.0, success_score))
    
    # If high quality, extract pattern
    if success_score > 0.7:
        pattern_data = generator.extract_pattern_from_thought(
            thought, 
            thought_type, 
            context
        )
        
        if pattern_data:
            # Create new pattern
            generator.create_new_pattern(
                thought_type,
                pattern_data["structure"],
                pattern_data["variables"]
            )
    
    # Record to prompt used (if available in context)
    if "used_pattern_id" in context:
        # Update success score
        pattern_id = context["used_pattern_id"]
        # Calculate delta based on score
        delta = (success_score - 0.5) * 0.1  # Small adjustments
        generator.update_pattern_score(pattern_id, delta)

def evolve_prompt_patterns() -> Dict[str, Any]:
    """
    Periodically evolve prompt patterns based on usage statistics
    Returns statistics about the evolution
    """
    generator = DynamicPromptGenerator()
    return generator.evolve_patterns()

def init_prompt_system() -> None:
    """
    Initialize the dynamic prompt system
    """
    # Just load/initialize the patterns
    generator = DynamicPromptGenerator()
    # Make sure we have patterns for all thought types
    if "reflection" not in generator.patterns:
        generator.patterns["reflection"] = generator._init_reflection_patterns()
    if "dream" not in generator.patterns:
        generator.patterns["dream"] = generator._init_dream_patterns()
    if "monologue" not in generator.patterns:
        generator.patterns["monologue"] = generator._init_monologue_patterns()
    if "existential_question" not in generator.patterns:
        generator.patterns["existential_question"] = generator._init_existential_patterns()
    
    # Save to ensure all types are available
    generator._save_patterns(generator.patterns)
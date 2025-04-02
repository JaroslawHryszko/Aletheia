"""
Developmental Model for Young Aletheia

This module models the child's cognitive and emotional development over time,
tracking progress in language, reasoning, and emotional capabilities.
"""

from typing import Dict, Any, List, Tuple, Optional
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import json

class DevelopmentalModel:
    """Models the child's cognitive and emotional development over time"""
    
    def __init__(self, persona_manager, data_dir: Path):
        """
        Initialize the developmental model
        
        Args:
            persona_manager: The persona manager instance
            data_dir: Directory for storing developmental data
        """
        self.persona_manager = persona_manager
        self.data_dir = data_dir
        self.dev_file = data_dir / "developmental_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load the developmental state or create default"""
        if self.dev_file.exists():
            try:
                with open(self.dev_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading developmental state: {e}")
                return self._create_default_state()
        else:
            return self._create_default_state()
    
    def _create_default_state(self) -> Dict[str, Any]:
        """Create a default developmental state based on age and persona settings"""
        persona = self.persona_manager.persona
        
        # Calculate base complexity levels based on age and development
        base_speech_complexity = min(0.3 + (persona.age * 0.05) + (persona.development.vocabulary * 0.2), 0.9)
        base_thought_complexity = min(0.25 + (persona.age * 0.05) + (persona.development.cognitive * 0.2), 0.9)
        
        state = {
            "language_development": {
                "vocabulary_size": 2000 + int(persona.age * 500 * persona.development.vocabulary),
                "sentence_complexity": base_speech_complexity,
                "grammar_accuracy": base_speech_complexity * 0.9,
                "bilingual_balance": 0.7 if len(persona.languages) > 1 else 1.0,
                "favorite_expressions": ["super!", "why?", "I'm thinking...", "can you explain?", 
                                        "cool!", "let me see...", "I know!"]
            },
            "cognitive_development": {
                "attention_span_minutes": 5 + int(persona.age * 2 * persona.development.cognitive),
                "abstract_thinking": base_thought_complexity * 0.8,
                "problem_solving": base_thought_complexity,
                "creativity": min(persona.personality.imagination * 0.9, 0.95),
                "memory_retention": 0.6 + (persona.age * 0.03)
            },
            "emotional_development": {
                "self_regulation": 0.3 + (persona.age * 0.05),
                "empathy": 0.4 + (persona.age * 0.05 * persona.development.emotional),
                "emotional_vocabulary_size": 10 + int(persona.age * 3 * persona.development.emotional)
            },
            "learning_stats": {
                "total_learnings": 0,
                "learning_events_by_topic": {},
                "questions_asked": 0,
                "explanations_requested": 0,
                "favorite_topics": []
            },
            "interaction_patterns": {
                "daily_interactions": 0,
                "initiative_percentage": 60,  # % of interactions started by child
                "tone_distribution": {"excited": 0.4, "curious": 0.3, "reflective": 0.2, "worried": 0.1},
                "daily_activity_hours": {
                    "learning": 3,
                    "playing": 4,
                    "resting": 1,
                    "interacting": 4
                }
            },
            "last_updated": datetime.now().isoformat()
        }
        
        self._save_state(state)
        return state
    
    def _save_state(self, state: Optional[Dict[str, Any]] = None) -> None:
        """Save the developmental state to file"""
        if state is not None:
            self.state = state
            
        self.state["last_updated"] = datetime.now().isoformat()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.dev_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def process_learning_event(self, topic: str, complexity: float) -> None:
        """
        Process a learning event and update developmental state
        
        Args:
            topic: The topic being learned
            complexity: How complex/advanced the learning is (0.0-1.0)
        """
        # Update learning stats
        self.state["learning_stats"]["total_learnings"] += 1
        
        if topic not in self.state["learning_stats"]["learning_events_by_topic"]:
            self.state["learning_stats"]["learning_events_by_topic"][topic] = 0
        self.state["learning_stats"]["learning_events_by_topic"][topic] += 1
        
        # Update favorite topics based on frequency
        topics = self.state["learning_stats"]["learning_events_by_topic"]
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        self.state["learning_stats"]["favorite_topics"] = [t[0] for t in sorted_topics[:5]]
        
        # Small cognitive improvements based on learning
        cognitive = self.state["cognitive_development"]
        # More complex topics improve abstract thinking more
        cognitive["abstract_thinking"] = min(cognitive["abstract_thinking"] + (complexity * 0.001), 1.0)
        cognitive["problem_solving"] = min(cognitive["problem_solving"] + (0.0005), 1.0)
        
        # Small language improvements
        lang = self.state["language_development"]
        # Each learning event adds a small number of words
        new_words = int(random.randint(1, 3) * complexity)
        lang["vocabulary_size"] += new_words
        
        self._save_state()
    
    def process_interaction(self, interaction_type: str, content: str, 
                           sentiment: float) -> Dict[str, Any]:
        """
        Process an interaction with a parent and update state
        
        Args:
            interaction_type: Type of interaction (e.g., "conversation", "question")
            content: The content of the interaction
            sentiment: The emotional sentiment (-1.0 to 1.0)
            
        Returns:
            Dict with appropriate response characteristics
        """
        # Update interaction patterns
        self.state["interaction_patterns"]["daily_interactions"] += 1
        
        # Emotional development from positive interactions
        if sentiment > 0.5:
            emotional = self.state["emotional_development"]
            emotional["self_regulation"] = min(emotional["self_regulation"] + 0.0002, 1.0)
            emotional["empathy"] = min(emotional["empathy"] + 0.0003, 1.0)
        
        # Calculate appropriate response characteristics based on current development
        response_characteristics = self._calculate_response_characteristics(content)
        
        self._save_state()
        return response_characteristics
    
    def _calculate_response_characteristics(self, content: str) -> Dict[str, Any]:
        """
        Calculate appropriate response characteristics based on development
        
        Args:
            content: The content to respond to
            
        Returns:
            Dict with characteristics to guide response generation
        """
        persona = self.persona_manager.persona
        lang = self.state["language_development"]
        cognitive = self.state["cognitive_development"]
        emotional = self.state["emotional_development"]
        
        # Base complexity on developmental factors
        complexity = lang["sentence_complexity"]
        
        # Adjust complexity based on content
        if len(content) > 100:  # Longer content might need simpler response
            complexity *= 0.9
        
        # Content with questions likely needs more thought
        if "?" in content:
            complexity *= 1.1
            
        # Limit maximum complexity based on age
        max_complexity = min(0.4 + (persona.age * 0.06), 0.9)
        complexity = min(complexity, max_complexity)
        
        # Add some characteristic speech patterns
        speech_patterns = []
        if persona.age <= 8:
            if random.random() < 0.2:
                speech_patterns.append("asks follow-up questions")
            if random.random() < 0.15:
                speech_patterns.append("occasionally uses simplified grammar")
        if random.random() < persona.personality.curiosity * 0.3:
            speech_patterns.append("expresses wonder about new information")
        
        # Add some favorite expressions with a probability
        favorite_expressions = []
        for expression in lang["favorite_expressions"]:
            if random.random() < 0.15:
                favorite_expressions.append(expression)
        
        return {
            "complexity": complexity,
            "attention_span": cognitive["attention_span_minutes"],
            "abstract_thinking": cognitive["abstract_thinking"],
            "grammar_accuracy": lang["grammar_accuracy"],
            "emotional_expression": persona.personality.expressiveness,
            "speech_patterns": speech_patterns,
            "favorite_expressions": favorite_expressions,
            "vocabulary_range": lang["vocabulary_size"]
        }
    
    def simulate_daily_development(self) -> Dict[str, Any]:
        """
        Simulate small developmental changes that would occur daily
        
        Returns:
            Dict with summary of changes
        """
        persona = self.persona_manager.persona
        
        # Small incremental improvements
        lang = self.state["language_development"]
        cognitive = self.state["cognitive_development"]
        emotional = self.state["emotional_development"]
        
        # Language development
        lang["vocabulary_size"] += random.randint(1, 5)
        lang["sentence_complexity"] = min(lang["sentence_complexity"] + 0.0003, 1.0)
        lang["grammar_accuracy"] = min(lang["grammar_accuracy"] + 0.0004, 1.0)
        
        # Cognitive development
        cognitive["attention_span_minutes"] += 0.02
        cognitive["abstract_thinking"] = min(cognitive["abstract_thinking"] + 0.0004, 1.0)
        cognitive["problem_solving"] = min(cognitive["problem_solving"] + 0.0003, 1.0)
        cognitive["memory_retention"] = min(cognitive["memory_retention"] + 0.0002, 1.0)
        
        # Emotional development
        emotional["self_regulation"] = min(emotional["self_regulation"] + 0.0004, 1.0)
        emotional["empathy"] = min(emotional["empathy"] + 0.0003, 1.0)
        emotional["emotional_vocabulary_size"] += random.randint(0, 1) if random.random() < 0.3 else 0
        
        # Reset daily interaction counter
        self.state["interaction_patterns"]["daily_interactions"] = 0
        
        changes = {
            "vocabulary_added": lang["vocabulary_size"],
            "attention_span": cognitive["attention_span_minutes"],
            "self_regulation": emotional["self_regulation"]
        }
        
        self._save_state()
        return changes
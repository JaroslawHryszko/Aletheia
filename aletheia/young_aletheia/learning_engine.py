"""
Learning Engine for Young Aletheia

This module manages the child's learning activities and internet exploration,
ensuring safe and appropriate learning experiences.
"""

from typing import Dict, Any, List, Optional
import random
import re
from datetime import datetime
import json
import asyncio
from pathlib import Path

class LearningEngine:
    """Manages the child's learning activities and internet exploration"""
    
    def __init__(self, persona_manager, dev_model, data_dir: Path):
        """
        Initialize the learning engine
        
        Args:
            persona_manager: The persona manager instance
            dev_model: The developmental model instance
            data_dir: Directory for storing learning data
        """
        self.persona_manager = persona_manager
        self.dev_model = dev_model
        self.data_dir = data_dir
        self.learning_log_file = data_dir / "learning_log.json"
        self.learning_log = self._load_learning_log()
        self.api_keys = self._load_api_keys()
    
    def _load_learning_log(self) -> Dict[str, Any]:
        """Load the learning log or create default"""
        if self.learning_log_file.exists():
            try:
                with open(self.learning_log_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading learning log: {e}")
                return self._create_default_learning_log()
        else:
            return self._create_default_learning_log()
    
    def _create_default_learning_log(self) -> Dict[str, Any]:
        """Create a default learning log"""
        return {
            "learning_events": [],
            "topics_explored": {},
            "favorite_sources": {},
            "questions_asked": [],
            "last_learning_time": datetime.now().isoformat(),
            "daily_learning_count": 0
        }
    
    def _save_learning_log(self):
        """Save the learning log to file"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.learning_log_file, "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2, ensure_ascii=False)
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys for learning services"""
        api_keys_file = self.data_dir.parent.parent / ".env"
        if not api_keys_file.exists():
            return {}
        
        api_keys = {}
        try:
            with open(api_keys_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.strip().split("=", 1)
                        if key.endswith("_API_KEY"):
                            api_keys[key] = value
            return api_keys
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}
    
    def generate_learning_activity(self) -> Dict[str, Any]:
        """
        Generate a natural learning activity based on the child's interests
        
        Returns:
            Dict with details about the generated learning activity
        """
        persona = self.persona_manager.persona
        
        # Select an interest to explore
        interest = random.choice(persona.interests)
        
        # Generate a topic within that interest
        topics_by_interest = {
            "animals": ["cats", "dogs", "elephants", "dinosaurs", "sea creatures", "birds", "insects"],
            "space": ["planets", "stars", "astronauts", "rockets", "the moon", "the sun", "black holes"],
            "drawing": ["colors", "shapes", "art techniques", "famous painters", "drawing animals"],
            "books": ["fairy tales", "adventure stories", "character types", "story elements"],
            "nature": ["trees", "flowers", "weather", "seasons", "mountains", "oceans"]
        }
        
        # Extract the main category from the interest
        main_category = interest.split(",")[0].strip().lower()
        
        # Get topics for the category or use default
        topics = topics_by_interest.get(main_category, ["interesting facts", "basic concepts", "fun information"])
        topic = random.choice(topics)
        
        # Track topic exploration
        if topic not in self.learning_log["topics_explored"]:
            self.learning_log["topics_explored"][topic] = 0
        self.learning_log["topics_explored"][topic] += 1
        
        # Create learning activity
        activity = {
            "interest": interest,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "learning_method": random.choice(["internet_search", "asking_parent", "observation", "connection_making"]),
            "complexity": min(0.3 + (persona.age * 0.05) + (random.random() * 0.2), 0.9)
        }
        
        # Add to learning log
        self.learning_log["learning_events"].append(activity)
        self.learning_log["daily_learning_count"] += 1
        self.learning_log["last_learning_time"] = activity["timestamp"]
        
        # Keep learning events manageable
        if len(self.learning_log["learning_events"]) > 100:
            self.learning_log["learning_events"] = self.learning_log["learning_events"][-100:]
        
        self._save_learning_log()
        
        return activity
    
    async def search_internet(self, query: str) -> Dict[str, Any]:
        """
        Search the internet for child-appropriate information
        
        Args:
            query: The search query
            
        Returns:
            Dict with search results and summary
        """
        # For safety, wrap all internet searches to ensure they're appropriate
        # and don't expose the child to harmful content
        
        safe_query = self._sanitize_query(query)
        
        # Determine which search method to use (simplified mock for now)
        try:
            # Use a search API to get information
            # In a production environment, you would use a real API with safe search enabled
            # This is a mock implementation
            search_result = await self._mock_search_results(safe_query)
            
            # Record the search
            self._record_search(safe_query, search_result)
            
            return search_result
        except Exception as e:
            print(f"Search error: {e}")
            return {
                "status": "error",
                "query": safe_query,
                "results": [],
                "summary": f"I couldn't find information about that right now. Maybe we can try again later?"
            }
    
    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize search query to ensure it's safe and appropriate
        
        Args:
            query: Original search query
            
        Returns:
            Sanitized query
        """
        # Remove unsafe keywords
        unsafe_terms = ['sex', 'porn', 'violence', 'gun', 'drugs', 'suicide', 'kill']
        sanitized_query = query
        for term in unsafe_terms:
            sanitized_query = re.sub(r'\b' + term + r'\b', '', sanitized_query, flags=re.IGNORECASE)
        
        # Add child-friendly terms
        sanitized_query += " for kids"
        
        return sanitized_query.strip()
    
    async def _mock_search_results(self, query: str) -> Dict[str, Any]:
        """
        Generate mock search results for development/testing purposes
        
        Args:
            query: Sanitized search query
            
        Returns:
            Dict with mock search results
        """
        # In a real implementation, use a child-safe search API
        interests = self.persona_manager.persona.interests
        
        # Create mock results based on the query and the child's interests
        mock_data = {
            "status": "success",
            "query": query,
            "results": []
        }
        
        # Check if query relates to child's interests
        for interest in interests:
            if any(term in query.lower() for term in interest.lower().split()):
                mock_data["results"].append({
                    "title": f"Fun facts about {interest} for kids",
                    "snippet": f"Did you know these amazing things about {interest}? Perfect for curious children!",
                    "safe_for_children": True
                })
        
        # Add some general results
        mock_data["results"].append({
            "title": f"Kids encyclopedia: {query}",
            "snippet": f"Learn about {query} in a way that's easy to understand for children.",
            "safe_for_children": True
        })
        
        # Prepare a simple summary
        if mock_data["results"]:
            summary = f"I found some information about {query}. "
            summary += mock_data["results"][0]["snippet"]
        else:
            summary = f"I couldn't find much about {query}. Maybe we could ask about something else?"
        
        mock_data["summary"] = summary
        
        return mock_data
    
    def _record_search(self, query: str, result: Dict[str, Any]):
        """
        Record search activity for learning tracking
        
        Args:
            query: The search query
            result: The search results
        """
        # Add to questions asked
        self.learning_log["questions_asked"].append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "success": result["status"] == "success" and len(result.get("results", [])) > 0
        })
        
        # Keep list manageable
        if len(self.learning_log["questions_asked"]) > 50:
            self.learning_log["questions_asked"] = self.learning_log["questions_asked"][-50:]
        
        self._save_learning_log()
        
        # Process this as a learning event if successful
        if result["status"] == "success" and result.get("results", []):
            topic = query
            content = result.get("summary", "I learned something new!")
            
            # Add to the child's learnings
            self.persona_manager.add_learning(topic, content, source="internet")
            
            # Process as developmental event
            self.dev_model.process_learning_event(topic, 0.7)
    
    def generate_learning_question(self) -> str:
        """
        Generate a question the child wants to ask based on curiosity
        
        Returns:
            Generated question
        """
        persona = self.persona_manager.persona
        
        # Base question templates
        question_templates = [
            "Why do {topic}?",
            "How do {topic} work?",
            "What makes {topic} {characteristic}?",
            "Why are {topic} important?",
            "Can you tell me about {topic}?",
            "What would happen if {scenario}?",
            "How many {topic} are there?",
            "Where do {topic} come from?"
        ]
        
        # Select a topic from interests or recently explored topics
        if random.random() < 0.7 and persona.interests:
            interest = random.choice(persona.interests)
            topic = interest.split(",")[0].strip()
        elif self.learning_log["topics_explored"]:
            # Use previously explored topic
            topic = random.choice(list(self.learning_log["topics_explored"].keys()))
        else:
            # Fallback topics
            topic = random.choice(["animals", "space", "dinosaurs", "rainbows", "the ocean"])
        
        # Select a template and fill it
        template = random.choice(question_templates)
        
        question = template.format(
            topic=topic,
            characteristic=random.choice(["special", "interesting", "different", "cool", "important"]),
            scenario=f"there were no {topic}"
        )
        
        # Record in learning log
        self.learning_log["questions_asked"].append({
            "query": question,
            "timestamp": datetime.now().isoformat(),
            "generated": True
        })
        
        self._save_learning_log()
        
        return question
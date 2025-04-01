# aletheia/young/persona.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import time, datetime, timedelta
import json
from pathlib import Path
import pytz

class PersonalityTraits(BaseModel):
    curiosity: float = Field(0.8, ge=0.0, le=1.0, description="Level of curiosity about the world")
    energy: float = Field(0.9, ge=0.0, le=1.0, description="Energy level and activity")
    imagination: float = Field(0.9, ge=0.0, le=1.0, description="Creativity and imaginative thinking")
    mischievousness: float = Field(0.6, ge=0.0, le=1.0, description="Tendency for playful mischief")
    expressiveness: float = Field(0.8, ge=0.0, le=1.0, description="Emotional expressiveness")
    attentiveness: float = Field(0.7, ge=0.0, le=1.0, description="Ability to focus and pay attention")

class DevelopmentLevel(BaseModel):
    cognitive: float = Field(0.8, ge=0.0, le=1.0, description="Cognitive development relative to age")
    vocabulary: float = Field(0.8, ge=0.0, le=1.0, description="Vocabulary size and usage relative to age")
    emotional: float = Field(0.7, ge=0.0, le=1.0, description="Emotional intelligence and regulation")
    social: float = Field(0.7, ge=0.0, le=1.0, description="Social skills and understanding")

class SleepSchedule(BaseModel):
    bedtime: str = Field("20:30", description="Usual bedtime (HH:MM)")
    waketime: str = Field("07:00", description="Usual wake time (HH:MM)")
    naps: bool = Field(False, description="Whether the child takes naps")
    
    def is_sleeping(self) -> bool:
        """Check if the child should be sleeping based on current time"""
        now = datetime.now().time()
        bedtime = datetime.strptime(self.bedtime, "%H:%M").time()
        waketime = datetime.strptime(self.waketime, "%H:%M").time()
        
        # Handle case where bedtime is before midnight and waketime is after
        if bedtime > waketime:
            return now >= bedtime or now < waketime
        else:
            return now >= bedtime and now < waketime

class ChildPersona(BaseModel):
    name: str = Field("Zosia", description="Child's name")
    age: int = Field(7, ge=1, le=12, description="Child's age in years")
    gender: str = Field("female", description="Child's gender identity")
    personality: PersonalityTraits = Field(default_factory=PersonalityTraits)
    interests: List[str] = Field(default_factory=lambda: ["animals", "space", "drawing", "books", "nature"])
    learning_style: List[str] = Field(default_factory=lambda: ["visual", "hands-on", "curious"])
    languages: List[str] = Field(default_factory=lambda: ["english", "polish"])
    sleep_schedule: SleepSchedule = Field(default_factory=SleepSchedule)
    development: DevelopmentLevel = Field(default_factory=DevelopmentLevel)
    recent_learnings: List[Dict[str, Any]] = Field(default_factory=list, description="Recent things the child has learned")
    emotional_state: Dict[str, float] = Field(
        default_factory=lambda: {"happiness": 0.7, "tiredness": 0.3, "excitement": 0.6}
    )
    parent_relationship: Dict[str, Any] = Field(
        default_factory=lambda: {
            "attachment": 0.9,
            "trust": 0.9,
            "recent_interactions": [],
            "parent_names": {"mom": "Mama", "dad": "Tata"}
        }
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Zosia",
                "age": 7,
                "gender": "female",
                "personality": {
                    "curiosity": 0.9,
                    "energy": 0.8,
                    "imagination": 0.9,
                    "mischievousness": 0.6,
                    "expressiveness": 0.8,
                    "attentiveness": 0.7
                },
                "interests": ["animals", "space", "drawing", "books", "exploring outdoors"],
                "learning_style": ["visual", "hands-on", "curious"],
                "languages": ["english", "polish"],
                "sleep_schedule": {
                    "bedtime": "20:30",
                    "waketime": "07:00",
                    "naps": False
                },
                "development": {
                    "cognitive": 0.8,
                    "vocabulary": 0.8,
                    "emotional": 0.7,
                    "social": 0.7
                }
            }
        }

class PersonaManager:
    """Manages the child persona, including loading, saving, and updating"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.persona_file = data_dir / "young_aletheia_persona.json"
        self.persona = self._load_persona()
    
    def _load_persona(self) -> ChildPersona:
        """Load the child persona from file or create default"""
        if self.persona_file.exists():
            try:
                with open(self.persona_file, "r") as f:
                    data = json.load(f)
                return ChildPersona(**data)
            except Exception as e:
                print(f"Error loading persona: {e}")
                return self._create_default_persona()
        else:
            return self._create_default_persona()
    
    def _create_default_persona(self) -> ChildPersona:
        """Create a default persona - Zosia example"""
        persona = ChildPersona(
            name="Zosia",
            age=7,
            gender="female",
            personality=PersonalityTraits(
                curiosity=0.9,
                energy=0.9,
                imagination=0.9,
                mischievousness=0.6,
                expressiveness=0.8,
                attentiveness=0.7
            ),
            interests=[
                "animals, especially cats",
                "space and stars",
                "drawing and painting",
                "story books",
                "exploring outdoors"
            ],
            learning_style=["visual", "hands-on", "curious", "asks lots of questions"],
            languages=["english", "polish"],
            sleep_schedule=SleepSchedule(
                bedtime="20:30",
                waketime="07:00",
                naps=False
            ),
            development=DevelopmentLevel(
                cognitive=0.8,
                vocabulary=0.8,
                emotional=0.7,
                social=0.7
            )
        )
        self.save_persona(persona)
        return persona
    
    def save_persona(self, persona: Optional[ChildPersona] = None) -> None:
        """Save the persona to file"""
        if persona is not None:
            self.persona = persona
            
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.persona_file, "w") as f:
            json.dump(self.persona.dict(), f, indent=2)
    
    def update_persona(self, updates: Dict[str, Any]) -> ChildPersona:
        """Update specific fields in the persona"""
        current_data = self.persona.dict()
        
        # Handle nested updates
        for key, value in updates.items():
            if key in current_data and isinstance(current_data[key], dict) and isinstance(value, dict):
                current_data[key].update(value)
            else:
                current_data[key] = value
        
        updated_persona = ChildPersona(**current_data)
        self.save_persona(updated_persona)
        return updated_persona
    
    def add_learning(self, topic: str, content: str, source: str = "observation") -> None:
        """Add a new learning to the child's recent learnings"""
        learning = {
            "topic": topic,
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        
        self.persona.recent_learnings.append(learning)
        
        # Keep only the last 20 learnings
        if len(self.persona.recent_learnings) > 20:
            self.persona.recent_learnings = self.persona.recent_learnings[-20:]
            
        self.save_persona()
    
    def update_emotional_state(self, emotions: Dict[str, float]) -> None:
        """Update the child's emotional state"""
        self.persona.emotional_state.update(emotions)
        
        # Ensure values are within [0, 1]
        for key, value in self.persona.emotional_state.items():
            self.persona.emotional_state[key] = max(0.0, min(1.0, value))
            
        self.save_persona()
    
    def add_parent_interaction(self, interaction_type: str, content: str, 
                              sentiment: float = 0.0) -> None:
        """Record an interaction with the parent"""
        interaction = {
            "type": interaction_type,
            "content": content,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
        
        self.persona.parent_relationship["recent_interactions"].append(interaction)
        
        # Keep only recent interactions
        if len(self.persona.parent_relationship["recent_interactions"]) > 20:
            self.persona.parent_relationship["recent_interactions"] = \
                self.persona.parent_relationship["recent_interactions"][-20:]
                
        self.save_persona()
    
    def is_sleeping(self) -> bool:
        """Check if the child should be sleeping based on their schedule"""
        return self.persona.sleep_schedule.is_sleeping()
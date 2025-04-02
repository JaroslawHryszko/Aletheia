"""
Integration Module for Young Aletheia

This module integrates Young Aletheia functionality into the main Aletheia system,
coordinating the various components and managing background tasks.
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI
import asyncio
from pathlib import Path
from datetime import datetime
import random
import re

from aletheia.config import CONFIG
from aletheia.utils.logging import log_event

class YoungAletheiaIntegration:
    """Integrates Young Aletheia functionality into the main Aletheia system"""
    
    def __init__(self, app: Optional[FastAPI] = None):
        """
        Initialize the Young Aletheia integration
        
        Args:
            app: Optional FastAPI application to integrate with
        """
        # Base paths
        self.base_dir = Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._init_components()
        
        # Setup tasks
        self.cycle_task = None
        self.growth_task = None
        
        # Add to FastAPI if provided
        if app:
            self.add_to_app(app)
    
    def _init_components(self):
        """Initialize all child components"""
        from aletheia.young_aletheia.persona import PersonaManager
        from aletheia.young_aletheia.developmental_model import DevelopmentalModel
        from aletheia.young_aletheia.message_generator import ChildMessageGenerator
        from aletheia.young_aletheia.learning_engine import LearningEngine
        
        # Initialize in order (with dependencies)
        self.persona_manager = PersonaManager(self.data_dir)
        self.dev_model = DevelopmentalModel(self.persona_manager, self.data_dir)
        self.message_generator = ChildMessageGenerator(self.persona_manager, self.dev_model)
        self.learning_engine = LearningEngine(self.persona_manager, self.dev_model, self.data_dir)
        
        # Initialize telegram bot if configuration exists
        from young_aletheia.telegram_bot import YoungAletheiaTelegramBot
        self.telegram_bot = YoungAletheiaTelegramBot(
            CONFIG,
            self.persona_manager,
            self.dev_model,
            self.message_generator,
            self.learning_engine
        )
    
    def add_to_app(self, app: FastAPI):
        """
        Add Young Aletheia to the FastAPI application
        
        Args:
            app: FastAPI application instance
        """
        from young_aletheia.interface import YoungAletheiaRouter
        
        # Create and setup router
        self.interface = YoungAletheiaRouter(
            app,
            self.persona_manager,
            self.dev_model,
            self.message_generator,
            self.learning_engine
        )
        
        # Register app lifecycle events
        @app.on_event("startup")
        async def startup_young_aletheia():
            # Start background tasks
            self.cycle_task = asyncio.create_task(self._run_daily_cycle())
            self.growth_task = asyncio.create_task(self._run_growth_cycle())
            
            # Start telegram bot if configured
            if self.telegram_bot.token:
                asyncio.create_task(self.telegram_bot.start_bot())
            
            log_event("Young Aletheia started", {
                "persona": self.persona_manager.persona.name,
                "age": self.persona_manager.persona.age
            })
        
        @app.on_event("shutdown")
        async def shutdown_young_aletheia():
            # Cancel background tasks
            if self.cycle_task:
                self.cycle_task.cancel()
            if self.growth_task:
                self.growth_task.cancel()
            
            # Stop telegram bot
            await self.telegram_bot.stop_bot()
            
            log_event("Young Aletheia shut down")
    
    async def _run_daily_cycle(self):
        """Run the daily cycle simulation (sleep/wake, needs, etc.)"""
        try:
            while True:
                persona = self.persona_manager.persona
                
                # Check time of day and update emotional state accordingly
                now = datetime.now().time()
                bedtime = datetime.strptime(persona.sleep_schedule.bedtime, "%H:%M").time()
                waketime = datetime.strptime(persona.sleep_schedule.waketime, "%H:%M").time()
                
                # Near bedtime, increase tiredness
                if (now > datetime.strptime("19:00", "%H:%M").time() and 
                    now < bedtime):
                    self.persona_manager.update_emotional_state({
                        "tiredness": min(persona.emotional_state.get("tiredness", 0) + 0.1, 1.0)
                    })
                
                # Near wake time, decrease tiredness
                if (now > waketime and 
                    now < datetime.strptime("09:00", "%H:%M").time()):
                    self.persona_manager.update_emotional_state({
                        "tiredness": max(persona.emotional_state.get("tiredness", 0) - 0.1, 0.0),
                        "happiness": min(persona.emotional_state.get("happiness", 0) + 0.05, 1.0)
                    })
                
                # Random emotional fluctuations throughout the day
                if random.random() < 0.3:
                    # Randomly select an emotion to adjust
                    emotion = random.choice(list(persona.emotional_state.keys()))
                    current = persona.emotional_state.get(emotion, 0.5)
                    
                    # Small random adjustment
                    adjustment = random.uniform(-0.1, 0.1)
                    new_value = max(0.0, min(1.0, current + adjustment))
                    
                    self.persona_manager.update_emotional_state({emotion: new_value})
                
                # Wait before next cycle
                await asyncio.sleep(1800)  # 30 minutes
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            log_event("Daily cycle error", {"error": str(e)})
            # Try to restart
            await asyncio.sleep(300)
            asyncio.create_task(self._run_daily_cycle())
    
    async def _run_growth_cycle(self):
        """Run the developmental growth cycle"""
        try:
            while True:
                # Simulate daily development every real-world day
                self.dev_model.simulate_daily_development()
                
                # Generate learning opportunities
                if not self.persona_manager.is_sleeping():
                    # Generate random learning activity
                    learning = self.learning_engine.generate_learning_activity()
                    
                    # Add to child's learnings
                    self.persona_manager.add_learning(
                        topic=learning["topic"],
                        content=f"Learned about {learning['topic']} through {learning['learning_method']}",
                        source=learning["learning_method"]
                    )
                    
                    # Process as developmental event
                    self.dev_model.process_learning_event(
                        learning["topic"],
                        learning["complexity"]
                    )
                    
                    # Occasionally share learning with parent via Telegram
                    if (random.random() < 0.3 and 
                        self.telegram_bot.token and 
                        learning["learning_method"] != "asking_parent"):
                        
                        # Generate learning message
                        context = {
                            "learning": learning["topic"],
                            "details": f"about {learning['topic']}"
                        }
                        message = self.message_generator.generate_message(context, "learning")
                        
                        # Send via Telegram
                        await self.telegram_bot.send_initiative_message(message)
                
                # Wait before next cycle
                await asyncio.sleep(14400)  # 4 hours
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            log_event("Growth cycle error", {"error": str(e)})
            # Try to restart
            await asyncio.sleep(300)
            asyncio.create_task(self._run_growth_cycle())
# aletheia/young/learning_engine.py
from typing import Dict, Any, List, Optional
import random
from datetime import datetime
import json
import requests
from pathlib import Path

class LearningEngine:
    """Manages the child's learning activities and internet exploration"""
    
    def __init__(self, persona_manager, dev_model, data_dir: Path):
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
                with open(self.learning_log_file, "r") as f:
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
        with open(self.learning_log_file, "w") as f:
            json.dump(self.learning_log, f, indent=2)
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys for learning services"""
        api_keys_file = self.data_dir.parent.parent / ".env"
        if not api_keys_file.exists():
            return {}
        
        api_keys = {}
        try:
            with open(api_keys_file, "r") as f:
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
        """Generate a natural learning activity based on the child's interests"""
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
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command"""
        try:
            persona = self.persona_manager.persona
            sleep_status = self.persona_manager.is_sleeping()
            
            # Format status message
            status_text = f"📊 {persona.name}'s Status\n\n"
            
            if sleep_status:
                status_text += f"😴 {persona.name} is currently sleeping. The usual wake time is {persona.sleep_schedule.waketime}.\n\n"
            else:
                # Add mood information
                moods = []
                for emotion, value in persona.emotional_state.items():
                    if value > 0.7:
                        moods.append(f"very {emotion}")
                    elif value > 0.4:
                        moods.append(f"{emotion}")
                
                if moods:
                    status_text += f"😊 Current mood: {', '.join(moods)}\n\n"
                
                # Add recent learning
                if persona.recent_learnings:
                    recent = persona.recent_learnings[-1]
                    status_text += f"🧠 Recently learned about: {recent['topic']}\n\n"
                
                # Add development info
                dev_state = self.dev_model.state
                status_text += (
                    f"📈 Development:\n"
                    f"- Vocabulary: ~{dev_state['language_development']['vocabulary_size']} words\n"
                    f"- Attention span: ~{int(dev_state['cognitive_development']['attention_span_minutes'])} minutes\n"
                )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=status_text
            )
        
        except Exception as e:
            self.logger.error(f"Error in status command: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, I couldn't get the status right now."
            )
    
    async def goodnight_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /goodnight command"""
        persona = self.persona_manager.persona
        
        # Update emotional state for bedtime
        self.persona_manager.update_emotional_state({"tiredness": 0.8})
        
        # Generate goodnight message
        goodnight_messages = [
            f"*yawns* Goodnight! 😴 I'm sleepy too...",
            f"Goodnight! Sweet dreams! 💤",
            f"Time for bed? Okay... *yawns* Goodnight!",
            f"*cuddles favorite stuffed animal* Nighty night!",
            f"Goodnight! Can you check for monsters under the bed? Just kidding! 😊"
        ]
        
        message = random.choice(goodnight_messages)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )
    
    async def goodmorning_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /goodmorning command"""
        persona = self.persona_manager.persona
        
        # Update emotional state for morning
        self.persona_manager.update_emotional_state({
            "tiredness": 0.2,
            "happiness": 0.8,
            "excitement": 0.7
        })
        
        # Generate morning message
        morning_context = {"time_of_day": "morning"}
        greeting = self.message_generator.generate_message(morning_context, "greeting")
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=greeting
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        # Update state
        self.last_message_time = datetime.now()
        self.conversation_active = True
        
        message_text = update.message.text
        
        # Check if child is sleeping
        if self.persona_manager.is_sleeping():
            sleeping_response = self.message_generator._generate_sleeping_response()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=sleeping_response
            )
            return
        
        # Detect language (simplified version)
        language = "english"
        polish_indicators = ["ą", "ę", "ó", "ś", "ć", "ż", "ź", "ń", "czy", "jest", "mam", "lubię"]
        if any(indicator in message_text.lower() for indicator in polish_indicators):
            language = "polish"
        
        # Prepare message context
        context = {
            "parent_message": message_text,
            "language": language
        }
        
        # If message looks like a question, try to learn from it
        if "?" in message_text:
            # Trigger a learning event if it's a question
            asyncio.create_task(self._process_learning_from_question(message_text))
        
        # Generate response
        response = self.message_generator.generate_message(context, "response")
        
        # Record interaction
        sentiment = self.message_generator._estimate_message_sentiment(message_text)
        self.persona_manager.add_parent_interaction("message", message_text, sentiment)
        
        # Process interaction for development
        self.dev_model.process_interaction("conversation", message_text, sentiment)
        
        # Send response (add typing indicator for realism)
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Delay based on message length (children don't type instantly)
        typing_delay = min(len(response) * 0.05, C] / 4.0
        await asyncio.sleep(typing_delay)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response
        )
    
    async def error_handler(self, update, context):
        """Handle errors in the bot"""
        self.logger.error(f"Error: {context.error} in update {update}")
    
    async def _process_learning_from_question(self, question: str):
        """Process potential learning from a parent's question"""
        try:
            # If it's a knowledge question, try to learn from it
            if any(term in question.lower() for term in ["what is", "how does", "why do", "tell me about"]):
                # Extract topic from question
                topic = question.replace("?", "").strip()
                topic = re.sub(r'^(what is|how does|why do|tell me about)\s+', '', topic, flags=re.IGNORECASE)
                
                # Simulate learning response
                search_result = await self.learning_engine._mock_search_results(topic)
                
                if search_result["status"] == "success":
                    # Add to learnings
                    self.persona_manager.add_learning(
                        topic=topic,
                        content=search_result["summary"],
                        source="parent_explanation"
                    )
                    
                    # Process as developmental event
                    self.dev_model.process_learning_event(topic, 0.8)
        except Exception as e:
            self.logger.error(f"Error processing learning from question: {e}")
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if not self.app:
            self.logger.warning("Cannot start bot: No token provided")
            return False
        
        try:
            # Start the bot
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            # Start initiative task
            asyncio.create_task(self._run_initiative_loop())
            
            self.logger.info(f"Bot started for {self.persona_manager.persona.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            return False
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.app:
            await self.app.stop()
            await self.app.shutdown()
    
    async def send_initiative_message(self, message: str):
        """Send a message initiated by the child"""
        if not self.app or not self.chat_id:
            return False
        
        try:
            # Send typing indicator for realism
            await self.app.bot.send_chat_action(
                chat_id=self.chat_id,
                action="typing"
            )
            
            # Delay based on message length (children don't type instantly)
            typing_delay = min(len(message) * 0.05, 4.0)
            await asyncio.sleep(typing_delay)
            
            # Send message
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            
            # Update initiative time
            self.last_initiative_time = datetime.now()
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending initiative message: {e}")
            return False
    
    async def _run_initiative_loop(self):
        """Run a loop that occasionally initiates conversation"""
        while True:
            try:
                # Wait between initiative checks
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Skip if child is sleeping
                if self.persona_manager.is_sleeping():
                    continue
                
                # Don't initiate if conversation is already active
                time_since_last_message = (datetime.now() - self.last_message_time).total_seconds()
                if time_since_last_message < 1800:  # 30 minutes
                    self.conversation_active = True
                else:
                    self.conversation_active = False
                
                # Don't initiate too frequently
                time_since_last_initiative = (datetime.now() - self.last_initiative_time).total_seconds()
                if time_since_last_initiative < 7200:  # 2 hours minimum between initiatives
                    continue
                
                # Random chance to initiate (higher when not in active conversation)
                initiative_chance = 0.05  # 5% chance every 5 minutes when conversation inactive
                if self.conversation_active:
                    initiative_chance = 0.01  # 1% chance when conversation active
                
                if random.random() < initiative_chance:
                    # Decide on initiative type
                    initiative_type = self._decide_initiative_type()
                    
                    # Generate message based on type
                    message = self.message_generator.generate_conversation_starter(initiative_type)
                    
                    if message:
                        await self.send_initiative_message(message)
            
            except Exception as e:
                self.logger.error(f"Error in initiative loop: {e}")
                await asyncio.sleep(300)  # Wait before retrying
    
    def _decide_initiative_type(self) -> str:
        """Decide what type of initiative to take"""
        persona = self.persona_manager.persona
        
        # Check for recent learnings to share
        if persona.recent_learnings and random.random() < 0.4:
            return "learning"
        
        # Check emotional state for special triggers
        if "boredom" in persona.emotional_state and persona.emotional_state["boredom"] > 0.7:
            return "bored"
        
        if random.random() < 0.3:
            return "question"
        
        return "general"
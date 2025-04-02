"""
Telegram Bot for Young Aletheia

This module implements a Telegram bot for interacting with Young Aletheia,
allowing parents to communicate with the child persona through Telegram.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pathlib import Path
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

class YoungAletheiaTelegramBot:
    """Telegram bot interface for Young Aletheia"""
    
    def __init__(self, config, persona_manager, dev_model, message_generator, learning_engine):
        """
        Initialize the Telegram bot
        
        Args:
            config: System configuration
            persona_manager: The persona manager instance
            dev_model: The developmental model instance
            message_generator: The message generator instance
            learning_engine: The learning engine instance
        """
        self.config = config
        self.persona_manager = persona_manager
        self.dev_model = dev_model
        self.message_generator = message_generator
        self.learning_engine = learning_engine
        
        # Bot configuration
        self.token = config.get("TELEGRAM_TOKEN", "")
        self.chat_id = config.get("CHAT_ID", "")
        
        # State tracking
        self.last_message_time = datetime.now()
        self.conversation_active = False
        self.last_initiative_time = datetime.now() - timedelta(hours=2)
        
        # Set up enhanced logging
        self.logger = logging.getLogger("young_aletheia_bot")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)  # Change to DEBUG for more verbose output
        
        # Validate token configuration
        if not self.token:
            self.logger.error("No Telegram token provided in configuration. Please check your .env or config.yaml file.")
            self.logger.debug(f"Configuration keys available: {list(config.keys())}")
            config_sample = {k: '...' for k in config.keys()}
            self.logger.debug(f"Configuration structure: {config_sample}")
        else:
            self.logger.info(f"Telegram token found, length: {len(self.token)}")
        
        # Validate chat ID
        if not self.chat_id:
            self.logger.warning("No CHAT_ID provided in configuration. This will limit bot's ability to initiate conversations.")
        
        # Initialize bot with better error handling
        if self.token:
            try:
                self.app = Application.builder().token(self.token).build()
                self.logger.info("Telegram bot application initialized successfully")
                self.setup_handlers()
            except Exception as e:
                self.logger.error(f"Error initializing Telegram bot application: {e}", exc_info=True)
                self.logger.debug(f"Token prefix: {self.token[:4]}..." if len(self.token) > 4 else "Token too short")
                self.app = None
        else:
            self.logger.warning("Bot functionality disabled due to missing token")
            self.app = None
    
    def setup_handlers(self):
        """Setup message handlers for the bot"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("goodnight", self.goodnight_command))
        self.app.add_handler(CommandHandler("goodmorning", self.goodmorning_command))
        
        # Message handler for regular text messages
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command
        
        Args:
            update: Telegram update
            context: Callback context
        """
        persona = self.persona_manager.persona
        
        # Send welcome message
        welcome_text = (
            f"👋 Hello! I'm {persona.name}, a {persona.age}-year-old {persona.gender}.\n\n"
            f"I love {', '.join(persona.interests[:3])}!\n\n"
            f"You can talk to me just like you would with a real child. "
            f"I learn, grow, and change over time based on our interactions."
        )
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text
        )
        
        # Generate an initial greeting
        if not self.persona_manager.is_sleeping():
            greeting = self.message_generator.generate_message({}, "greeting")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=greeting
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /status command
        
        Args:
            update: Telegram update
            context: Callback context
        """
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
        """
        Handle the /goodnight command
        
        Args:
            update: Telegram update
            context: Callback context
        """
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
        """
        Handle the /goodmorning command
        
        Args:
            update: Telegram update
            context: Callback context
        """
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
        """
        Handle incoming text messages
        
        Args:
            update: Telegram update
            context: Callback context
        """
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
        context_dict = {
            "parent_message": message_text,
            "language": language
        }
        
        # If message looks like a question, try to learn from it
        if "?" in message_text:
            # Trigger a learning event if it's a question
            asyncio.create_task(self._process_learning_from_question(message_text))
        
        # Generate response
        response = self.message_generator.generate_message(context_dict, "response")
        
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
        typing_delay = min(len(response) * 0.05, 4.0)
        await asyncio.sleep(typing_delay)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response
        )
    
    async def error_handler(self, update, context):
        """
        Handle errors in the bot
        
        Args:
            update: Telegram update
            context: Callback context with error
        """
        self.logger.error(f"Error: {context.error} in update {update}")
    
    async def _process_learning_from_question(self, question: str):
        """
        Process potential learning from a parent's question
        
        Args:
            question: The question asked by the parent
        """
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
        """
        Start the Telegram bot
        
        Returns:
            Boolean indicating success
        """
        if not self.app:
            self.logger.error("Cannot start bot: Application not initialized")
            return False
        
        try:
            # Log config status before starting
            self.logger.info(f"Starting bot with token: {'Available' if self.token else 'Not available'}")
            self.logger.info(f"Chat ID status: {'Available' if self.chat_id else 'Not available'}")
            
            # Start the bot
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            # Start initiative task
            asyncio.create_task(self._run_initiative_loop())
            
            self.logger.info(f"Bot started for {self.persona_manager.persona.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}", exc_info=True)
            
            # Check for common Telegram API errors
            error_text = str(e).lower()
            if "unauthorized" in error_text:
                self.logger.error("Error suggests invalid token. Please check your TELEGRAM_TOKEN value.")
            elif "network" in error_text or "connection" in error_text:
                self.logger.error("Network error. Please check your internet connection.")
            
            return False
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.app:
            await self.app.stop()
            await self.app.shutdown()
    
    async def send_initiative_message(self, message: str):
        """
        Send a message initiated by the child
        
        Args:
            message: The message to send
            
        Returns:
            Boolean indicating success
        """
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
        """
        Decide what type of initiative to take
        
        Returns:
            Initiative type string
        """
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
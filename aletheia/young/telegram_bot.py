# aletheia/young/telegram_bot.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pathlib import Path

class YoungAletheiaTelegramBot:
    """Telegram bot interface for Young Aletheia"""
    
    def __init__(self, config, persona_manager, dev_model, message_generator, learning_engine):
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
        
        # Logger
        self.logger = logging.getLogger("young_aletheia_bot")
        
        # Initialize bot
        if self.token:
            self.app = Application.builder().token(self.token).build()
            self.setup_handlers()
        else:
            self.logger.warning("No Telegram token provided, bot functionality disabled")
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
        """Handle the /start command"""
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
    
    async def
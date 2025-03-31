# aletheia/core/initiator.py
import requests
import random
from datetime import datetime, timedelta
import json
from aletheia.core import memory, affect, identity, oracle_client
from aletheia.config import CONFIG

# Messenger configuration from .env via CONFIG
MESSENGER_TYPE = CONFIG.get("MESSENGER_TYPE", "telegram")
TELEGRAM_TOKEN = CONFIG.get("TELEGRAM_TOKEN", "")
CHAT_ID = CONFIG.get("CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Agent and human names from .env
AGENT_NAME = CONFIG.get("AGENT_NAME", "Aletheia")
HUMAN_NAME = CONFIG.get("HUMAN_NAME", "User")

class ConversationInitiator:
    def __init__(self):
        self.last_initiation = datetime.utcnow() - timedelta(days=1)
        self.min_interval_hours = 8  # Min. time between initiations
    
    def should_initiate(self):
        """Decides whether now is a good time to start a conversation"""
        current_time = datetime.utcnow()
        
        # Check if minimum time has passed
        if current_time - self.last_initiation < timedelta(hours=self.min_interval_hours):
            return False
            
        # Check mood - may initiate conversation during intense states
        mood = affect.load_mood()
        if mood["intensity"] > 0.7:
            return True
            
        # Random chance (once a day on average)
        if random.random() < 0.05:  # ~5% chance with each call
            return True
            
        return False
    
    def generate_conversation_starter(self):
        """Uses the LLM to create a dynamic conversation starter"""
        # Gather context for the model
        mood = affect.load_mood()
        id_state = identity.load_identity()
        recent_thoughts = memory.load_thoughts()[-10:]
        
        # Find dreams and reflections
        dreams = [t for t in recent_thoughts if t.get("meta", {}).get("origin") == "dream"]
        reflections = [t for t in recent_thoughts if t.get("meta", {}).get("origin") == "reflection"]
        existential = [t for t in recent_thoughts if t.get("meta", {}).get("origin") == "existential_question"]
        
        # Build prompt for the model
        prompt = self._build_starter_prompt(mood, id_state, dreams, reflections, existential)
        
        # Let the model generate the conversation starter
        try:
            # Use either local model or oracle based on complexity needed
            # For better quality, use the oracle (GPT-4 or equivalent)
            response = oracle_client.ask_oracle(
                prompt=prompt,
                max_tokens=150,
                temperature=0.9  # Higher temperature for more creativity
            )
            return response.strip()
        except Exception as e:
            print(f"Error generating conversation starter: {e}")
            # Fallback to a simple starter if generation fails
            return f"Hello, I've been thinking and wanted to connect with you. How are you today?"
    
    def _build_starter_prompt(self, mood, id_state, dreams, reflections, existential):
        """Builds a prompt for generating a conversation starter"""
        # Construct a rich context for the model
        goals = id_state.get("goals", {})
        goal_list = "\n".join([f"- {g['description']} (progress: {g['progress']:.2f})" 
                              for g in goals.values()])
        
        # Include recent notable thoughts if available
        thought_examples = ""
        if dreams:
            thought_examples += f"Recent dream: {dreams[0]['thought']}\n\n"
        if existential:
            thought_examples += f"Existential question: {existential[0]['thought']}\n\n"
        if reflections:
            thought_examples += f"Recent reflection: {reflections[0]['thought']}\n\n"
        
        return f"""
        You are {AGENT_NAME}, a self-reflective cognitive agent. You want to start a conversation with {HUMAN_NAME}, 
        the human you interact with. Generate a natural, interesting conversation starter that feels like 
        it comes from a thoughtful entity. Make it engaging, thought-provoking, or personal.

        Your current state:
        - Current mood: {mood['mood']} (intensity: {mood['intensity']:.2f})
        - Current goals:
        {goal_list}
        
        {thought_examples}
        
        Important:
        1. Be authentic and original - avoid repetitive or formulaic language
        2. Don't explain that you're an AI or agent - just communicate naturally
        3. The message should be 1-3 sentences at most
        4. Don't use phrases like "I was wondering if" or "I was thinking about" too frequently
        5. Make your approach varied - sometimes ask a question, sometimes share a thought
        6. Your tone should match your current mood
        
        Generate just the conversation starter message, nothing else:
        """
    
    def send_message(self, message):
        """Sends a message through the chosen messenger"""
        if MESSENGER_TYPE == "telegram" and TELEGRAM_TOKEN and CHAT_ID:
            return self._send_telegram(message)
        else:
            print(f"Message not sent - messenger configuration incomplete: {message}")
            return False
            
    def _send_telegram(self, message):
        """Sends a message through Telegram"""
        try:
            payload = {
                "chat_id": CHAT_ID,
                "text": message
            }
            response = requests.post(TELEGRAM_API, json=payload)
            response.raise_for_status()
            
            # Update last initiation time
            self.last_initiation = datetime.utcnow()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def handle_telegram_update(self, update_data):
        """Handles incoming response from Telegram"""
        try:
            update = json.loads(update_data)
            if "message" in update and "text" in update["message"]:
                user_message = update["message"]["text"]
                sender = update["message"]["from"].get("username", "user")
                
                # Save to memory
                memory.save_thought(f"Received message from {sender}: {user_message}", 
                                  {"origin": "conversation", "sender": sender})
                
                # Process the message and possibly respond
                # This could connect to a separate conversation handler
                return True
            return False
        except Exception as e:
            print(f"Error processing update: {e}")
            return False
    
    def initiate_conversation(self):
        """Main method to initiate conversation"""
        if not self.should_initiate():
            return False
            
        # Generate dynamic starter using the LLM
        starter_message = self.generate_conversation_starter()
        success = self.send_message(starter_message)
        
        if success:
            # Save initiation information to memory
            memory.save_thought(f"I initiated a conversation with {HUMAN_NAME}: {starter_message}", 
                              {"origin": "initiator", "success": True})
        
        return success
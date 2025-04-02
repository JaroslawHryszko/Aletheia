"""
Message Generator for Young Aletheia

This module generates child-like messages based on the child's persona,
developmental level, and context of the conversation.
"""

import random
from typing import List, Dict, Any, Tuple, Optional
import re
import emoji
from datetime import datetime
from aletheia.core.multi_gpu_model_loader import load_model
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

class ChildMessageGenerator:
    """Generates child-like messages based on development level and persona"""
    
    def __init__(self, persona_manager, dev_model):
        """
        Initialize the message generator
        
        Args:
            persona_manager: The persona manager instance
            dev_model: The developmental model instance
        """
        self.persona_manager = persona_manager
        self.dev_model = dev_model
        self._model = None
        self._tokenizer = None
    
    def get_model(self):
        """Lazy-load the language model"""
        if self._model is None or self._tokenizer is None:
            self._model, self._tokenizer = load_model()
        return self._model, self._tokenizer
    
    def generate_message(self, context: Dict[str, Any], trigger: str = "general", 
                         prompt: Optional[str] = None) -> str:
        """
        Generate a child-like message based on context and developmental state
        
        Args:
            context: Dictionary with context information for generation
            trigger: The trigger type for the message (e.g., "greeting", "question")
            prompt: Optional pre-built prompt to use instead of building one
            
        Returns:
            Generated message text
        """
        persona = self.persona_manager.persona
        
        # Check if child would be sleeping
        if self.persona_manager.is_sleeping() and trigger != "nightmare":
            return self._generate_sleeping_response()
        
        # Get response characteristics based on development
        if "response_characteristics" not in context:
            context["response_characteristics"] = self.dev_model._calculate_response_characteristics("")
        
        characteristics = context["response_characteristics"]
        
        # Build the prompt based on persona and trigger
        if prompt is None:
            prompt = self._build_message_prompt(trigger, characteristics, context)
        
        # Generate the message
        model, tokenizer = self.get_model()
        
        # Tokenize and generate
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
        
        # Temperature based on personality expressiveness
        temperature = 0.7 + (persona.personality.expressiveness * 0.2)
        
        # Generate with appropriate parameters
        output = model.generate(
            input_ids, 
            max_new_tokens=150, 
            do_sample=True, 
            temperature=temperature,
            top_p=0.92
        )
        
        # Decode the generated message
        message = tokenizer.decode(output[0], skip_special_tokens=True)
        
        print(message)
        
        # Clean up the message and add child-like elements
        if CONFIG.get("ADD_KID_STYLE", True):
            message = self._process_generated_text(message, characteristics)
        
        # Log interaction for developmental tracking
        if "parent_message" in context:
            sentiment = self._estimate_message_sentiment(message)
            self.persona_manager.add_parent_interaction(
                interaction_type="response",
                content=message,
                sentiment=sentiment
            )
            
        return message
    
    def _build_message_prompt(self, trigger: str, characteristics: Dict[str, Any], 
                             context: Dict[str, Any]) -> str:
        """
        Build a prompt for message generation
        
        Args:
            trigger: Type of message to generate
            characteristics: Response characteristics from developmental model
            context: Additional context for generation
            
        Returns:
            Prompt string to feed to the language model
        """
        persona = self.persona_manager.persona
        
        # Base prompt with persona information
        prompt = f"""
You are roleplaying as {persona.name}, a {persona.age}-year-old {persona.gender} child.

{persona.name}'s personality:
- Curiosity: {'Very curious' if persona.personality.curiosity > 0.7 else 'Moderately curious'}
- Energy level: {'Very energetic' if persona.personality.energy > 0.7 else 'Moderately energetic'}
- Imagination: {'Highly imaginative' if persona.personality.imagination > 0.7 else 'Has a good imagination'}
- Expressiveness: {'Very expressive' if persona.personality.expressiveness > 0.7 else 'Expresses feelings clearly'}

{persona.name}'s interests include: {', '.join(persona.interests)}.

{persona.name}'s developmental level:
- Vocabulary size: around {characteristics['vocabulary_range']} words
- Sentence complexity: {self._translate_complexity_to_text(characteristics['complexity'])}
- Grammar accuracy: {self._translate_complexity_to_text(characteristics['grammar_accuracy'])}
- Abstract thinking: {self._translate_complexity_to_text(characteristics['abstract_thinking'])}

"""

        # Add specific context based on trigger type
        if trigger == "greeting":
            prompt += f"""
{persona.name} is greeting their parent with excitement and energy. 
{persona.name} might mention something they're excited about or a recent discovery.

Generate {persona.name}'s greeting message:
"""
        elif trigger == "question":
            prompt += f"""
{persona.name} is curious about something and wants to ask their parent about it.
{persona.name}'s question is about: {context.get('topic', 'something interesting')}.

Generate {persona.name}'s question message:
"""
        elif trigger == "response":
            parent_message = context.get('parent_message', '')
            prompt += f"""
{persona.name} is responding to their parent's message:
"{parent_message}"

{persona.name}'s response should be natural and reflect their personality and development level.

Generate {persona.name}'s response:
"""
        elif trigger == "learning":
            learning = context.get('learning', 'something interesting')
            prompt += f"""
{persona.name} just learned about {learning} and wants to share this with their parent.
{persona.name} is excited about this new knowledge and wants to tell them what they learned.

Generate {persona.name}'s message about this new learning:
"""
        elif trigger == "bored":
            prompt += f"""
{persona.name} is feeling a bit bored and reaching out to their parent.
{persona.name} might ask for something to do or suggest an activity they'd like to do together.

Generate {persona.name}'s message:
"""
        elif trigger == "nightmare":
            prompt += f"""
{persona.name} had a scary dream/nightmare and is messaging their parent about it.
{persona.name} is a bit upset and seeking comfort.

Generate {persona.name}'s message about the nightmare:
"""
        else:  # general message
            prompt += f"""
{persona.name} wants to chat with their parent about something on their mind.
{persona.name}'s message should reflect their personality, interests, and developmental level.

Generate {persona.name}'s message:
"""
        
        # Add language preference if specified
        #if "language" in context:
        #    if context["language"].lower() == "polish":
        #        prompt += "\nPlease generate the message in Polish language."
        #    else:
        #        prompt += "\nPlease generate the message in English language."
        
        return prompt
    
    def _process_generated_text(self, text: str, characteristics: Dict[str, Any]) -> str:
        """
        Process generated text to make it more child-like based on development
        
        Args:
            text: The raw generated text
            characteristics: The response characteristics
            
        Returns:
            Processed text with child-like features
        """
        persona = self.persona_manager.persona
        
        # Remove any non-message content (like prompt echoing)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if ':' in line and i < len(lines) - 1:
                # This might be a dialog format like "Child: message"
                # Take everything after this point
                text = '\n'.join(lines[i:])
                break
        
        # Remove any name prefixes
        text = re.sub(f"{persona.name}:", "", text)
        text = re.sub(r"^[A-Za-z]+:", "", text)
        
        # Clean up the text
        text = text.strip()
        
        # Add child-like modifications based on age and personality
        if persona.age <= 8:
            # Younger children may use more simple punctuation
            if random.random() < 0.3:
                text = self._simplify_punctuation(text)
            
            # Younger children may use more emojis
            if random.random() < 0.4:
                text = self._add_emojis(text)
            
            # Occasionally introduce minor spelling error for younger children
            # but only if grammar accuracy is not too high
            if random.random() < 0.2 and characteristics["grammar_accuracy"] < 0.8:
                text = self._introduce_spelling_error(text)
        
        # Add characteristic expressions
        if characteristics["favorite_expressions"] and random.random() < 0.3:
            expression = random.choice(characteristics["favorite_expressions"])
            if random.random() < 0.5 and not text.endswith(("!", "?", ".")):
                text += f" {expression}"
            elif random.random() < 0.3:
                text = f"{expression} {text}"
        
        return text
    
    def _simplify_punctuation(self, text: str) -> str:
        """
        Simplify punctuation to be more child-like
        
        Args:
            text: Original text
            
        Returns:
            Text with child-like punctuation
        """
        # Sometimes use multiple exclamation marks
        if "!" in text and random.random() < 0.5:
            text = re.sub(r"!", "!!" if random.random() < 0.5 else "!!!", text)
        
        # Sometimes use multiple question marks
        if "?" in text and random.random() < 0.4:
            text = re.sub(r"\?", "??" if random.random() < 0.7 else "???", text)
        
        return text
    
    def _add_emojis(self, text: str) -> str:
        """
        Add child-appropriate emojis to text
        
        Args:
            text: Original text
            
        Returns:
            Text with added emojis
        """
        child_emojis = [
            "😊", "😃", "😄", "🙂", "😁", "🤗", "🤔", "😮", "😎", "🌟", 
            "✨", "🐱", "🐶", "🦄", "🌈", "🍦", "🍭", "🎨", "📚", "🚀"
        ]
        
        # Add emoji at the end
        if random.random() < 0.6 and not text.endswith(tuple(child_emojis)):
            text += f" {random.choice(child_emojis)}"
        
        # Sometimes add emoji mid-sentence
        if len(text) > 30 and random.random() < 0.3:
            sentences = re.split(r'([.!?] )', text)
            if len(sentences) > 2:
                insert_point = random.randrange(0, len(sentences) - 1, 2)
                sentences.insert(insert_point + 1, f" {random.choice(child_emojis)} ")
                text = ''.join(sentences)
        
        return text
    
    def _introduce_spelling_error(self, text: str) -> str:
        """
        Introduce a minor, realistic child-like spelling error
        
        Args:
            text: Original text
            
        Returns:
            Text with a minor spelling error
        """
        words = text.split()
        if len(words) < 3:
            return text
            
        # Select a word to modify (avoid very short words)
        eligible_words = [i for i, word in enumerate(words) if len(word) > 3 
                         and word.isalpha() and i > 0]
        
        if not eligible_words:
            return text
            
        word_index = random.choice(eligible_words)
        word = words[word_index]
        
        # Choose error type
        error_type = random.choice(["swap", "double", "omit"])
        
        if error_type == "swap" and len(word) > 4:
            # Swap two adjacent letters
            pos = random.randint(0, len(word) - 2)
            new_word = word[:pos] + word[pos+1] + word[pos] + word[pos+2:]
        elif error_type == "double" and len(word) > 3:
            # Double a letter
            pos = random.randint(0, len(word) - 1)
            new_word = word[:pos] + word[pos] * 2 + word[pos+1:]
        else:
            # Omit a letter
            pos = random.randint(1, len(word) - 2)  # Avoid first/last letter for readability
            new_word = word[:pos] + word[pos+1:]
            
        words[word_index] = new_word
        return ' '.join(words)
    
    def _translate_complexity_to_text(self, complexity: float) -> str:
        """
        Translate a complexity value to descriptive text
        
        Args:
            complexity: Value between 0.0 and 1.0
            
        Returns:
            Descriptive text of the complexity level
        """
        if complexity < 0.3:
            return "basic"
        elif complexity < 0.5:
            return "developing"
        elif complexity < 0.7:
            return "intermediate"
        elif complexity < 0.85:
            return "advanced"
        else:
            return "very advanced"
    
    def _generate_sleeping_response(self) -> str:
        """
        Generate a response indicating the child is sleeping
        
        Returns:
            Message indicating the child is sleeping
        """
        persona = self.persona_manager.persona
        
        responses = [
            f"{persona.name} is currently sleeping. Bedtime is at {persona.sleep_schedule.bedtime} and wake time is around {persona.sleep_schedule.waketime}.",
            f"Shh! {persona.name} is sleeping right now. Children need their rest! Try again after {persona.sleep_schedule.waketime}.",
            f"{persona.name} is dreaming right now. You can talk to her again when she wakes up at around {persona.sleep_schedule.waketime}."
        ]
        
        return random.choice(responses)
    
    def _estimate_message_sentiment(self, message: str) -> float:
        """
        Estimate the sentiment of a message (simple heuristic)
        
        Args:
            message: The message text
            
        Returns:
            Sentiment value between 0.0 and 1.0
        """
        # Simple keyword based sentiment analysis
        positive_words = [
            "happy", "love", "wonderful", "great", "awesome", "fun", "exciting",
            "good", "nice", "cool", "amazing", "thank", "please", "smile", "laugh",
            "wesoły", "kocham", "wspaniały", "świetny", "fajny", "zabawa", "dobry",
            "miły", "super", "dziękuję", "proszę", "uśmiech", "śmiech", "radość"
        ]
        
        negative_words = [
            "sad", "bad", "angry", "upset", "scared", "afraid", "worried", "hate",
            "boring", "mean", "cry", "hurt", "smutny", "zły", "przestraszony",
            "boję", "zmartwiony", "nienawidzę", "nudny", "płacz", "boli"
        ]
        
        # Count occurrences
        positive_count = sum(1 for word in positive_words if word.lower() in message.lower())
        negative_count = sum(1 for word in negative_words if word.lower() in message.lower())
        
        # Calculate sentiment score (0.5 is neutral)
        total = positive_count + negative_count
        if total == 0:
            return 0.5
            
        sentiment = 0.5 + ((positive_count - negative_count) / (total * 2))
        return max(0.0, min(1.0, sentiment))
    
    def generate_conversation_starter(self, trigger_type: str = None) -> str:
        """
        Generate a conversation starter based on the child's persona and state
        
        Args:
            trigger_type: Optional trigger type to use
            
        Returns:
            Generated conversation starter or None if not appropriate
        """
        persona = self.persona_manager.persona
        
        # Check if child would be sleeping
        if self.persona_manager.is_sleeping():
            return None  # Don't initiate conversation while sleeping
        
        # Determine trigger type if not specified
        if trigger_type is None:
            # Default distribution of conversation starters
            triggers = [
                ("learning", 0.3),      # Sharing something learned
                ("question", 0.25),     # Asking a question
                ("greeting", 0.15),     # Simple greeting
                ("bored", 0.15),        # Feeling bored
                ("general", 0.15)       # General chat
            ]
            
            # Adjust probabilities based on emotional state
            if "tiredness" in persona.emotional_state and persona.emotional_state["tiredness"] > 0.7:
                # Less likely to start conversations when tired
                return None if random.random() < 0.7 else self.generate_message({"topic": "being tired"}, "general")
                
            if "excitement" in persona.emotional_state and persona.emotional_state["excitement"] > 0.8:
                # More likely to share learning when excited
                triggers = [("learning", 0.5), ("question", 0.2), ("greeting", 0.2), ("general", 0.1)]
            
            # Weighted random selection
            total = sum(weight for _, weight in triggers)
            r = random.uniform(0, total)
            upto = 0
            for trigger, weight in triggers:
                upto += weight
                if upto >= r:
                    trigger_type = trigger
                    break
        
        # Context based on trigger type
        context = {}
        
        if trigger_type == "learning":
            # Get a recent learning to share
            if persona.recent_learnings:
                learning = random.choice(persona.recent_learnings)
                context["learning"] = learning["topic"]
                context["details"] = learning["content"]
            else:
                # Default learning topics if none available
                topics = ["animals", "space", "a cool fact", "something at school"]
                context["learning"] = random.choice(topics)
        
        elif trigger_type == "question":
            # Generate a question about an interest
            context["topic"] = random.choice(persona.interests)
        
        # Set language randomly if bilingual
        if len(persona.languages) > 1:
            context["language"] = random.choice(persona.languages)
        
        # Get response characteristics
        context["response_characteristics"] = self.dev_model._calculate_response_characteristics("")
        
        # Generate the message
        return self.generate_message(context, trigger_type)
import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR.parent / ".env")

CONFIG = {
    # === Server ===
    "API_PORT": int(os.getenv("API_PORT", 8000)),

    # === Reflection Scheduling ===
    "REFLECTION_INTERVAL": int(os.getenv("REFLECTION_INTERVAL", 300)),  # seconds
    "DREAM_INTERVAL": int(os.getenv("DREAM_INTERVAL", 900)),
    "MONOLOGUE_INTERVAL": int(os.getenv("MONOLOGUE_INTERVAL", 1200)),
    "EXISTENTIAL_INTERVAL": int(os.getenv("EXISTENTIAL_INTERVAL", 1800)),
    "PULSE_INTERVAL": int(os.getenv("PULSE_INTERVAL", 60)),

    # === LLM Backends ===
    "USE_LOCAL_MODEL": os.getenv("USE_LOCAL_MODEL", "true").lower() == "true",
    "MULTI_GPU": os.getenv("MULTI_GPU", "true").lower() == "true",
    "LOCAL_MODEL_NAME": os.getenv("LOCAL_MODEL_NAME", "mistral-7b"),
    
    # === OpenAI (external oracle)
    "GPT_MODEL": os.getenv("GPT_MODEL", "gpt-4"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),

    # === Metadata ===
    "AGENT_NAME": os.getenv("AGENT_NAME", "Aletheia"),
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "local"),
    
    # === External APIs ===
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY", ""),
}

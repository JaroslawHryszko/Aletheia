# aletheia/core/perception.py
import requests
import json
from datetime import datetime
from aletheia.core import memory
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

# Get API key from configuration (loaded from .env)
NEWS_API_KEY = CONFIG.get("NEWS_API_KEY", "")

SOURCES = [
    {"name": "news_api", "url": f"https://newsapi.org/v2/top-headlines?country=pl&apiKey={NEWS_API_KEY}"},
]

def fetch_external_data():
    if not NEWS_API_KEY:
        log_event("Perception error", {"error": "Missing API key in configuration"})
        return []
        
    perceptions = []
    for source in SOURCES:
        try:
            response = requests.get(source["url"])
            data = response.json()
            # Process data and save key information
            for item in data.get("articles", [])[:5]:  # Limit to 5 news items
                perception = f"[External: {source['name']}] {item['title']}: {item['description']}"
                perceptions.append(perception)
                memory.save_thought(perception, {"origin": "perception", "source": source["name"]})
            
            log_event("External perception complete", {"source": source["name"]})
        except Exception as e:
            log_event("Perception error", {"error": str(e), "source": source["name"]})
    
    return perceptions
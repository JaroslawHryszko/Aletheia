# Implementing "Young Aletheia"

This document provides a step-by-step guide to implementing the "Young Aletheia" feature in the existing Aletheia codebase.

## 1. Directory Structure

First, create the necessary directory structure:

```bash
mkdir -p aletheia/young/data
mkdir -p aletheia/young/templates
mkdir -p aletheia/young/static
```

## 2. Install Required Dependencies

Add these to your requirements.txt:

```
python-telegram-bot>=13.0
emoji>=2.0.0
jinja2>=3.0.0
```

## 3. Files to Create

### aletheia/young/__init__.py

Create this file with the initialization function:

```python
def initialize_young_aletheia(app=None):
    """Initialize the Young Aletheia system"""
    from aletheia.young.integration import YoungAletheiaIntegration
    
    try:
        # Create the integration
        integration = YoungAletheiaIntegration(app)
        
        print("✅ Young Aletheia initialized successfully")
        return integration
    except Exception as e:
        print(f"❌ Error initializing Young Aletheia: {e}")
        return None
```

### aletheia/young/persona.py

Create this file with the persona management code:

```python
# Insert the complete code from the PersonaManager class shown earlier
```

### aletheia/young/developmental_model.py

Create this file with the developmental model code:

```python
# Insert the complete code from the DevelopmentalModel class shown earlier
```

### aletheia/young/message_generator.py

Create this file with the message generation code:

```python
# Insert the complete code from the ChildMessageGenerator class shown earlier
```

### aletheia/young/learning_engine.py

Create this file with the learning engine code:

```python
# Insert the complete code from the LearningEngine class shown earlier
```

### aletheia/young/telegram_bot.py

Create this file with the Telegram bot code:

```python
# Insert the complete code from the YoungAletheiaTelegramBot class shown earlier
```

### aletheia/young/interface.py

Create this file with the REST API and web interface code:

```python
# Insert the complete code from the YoungAletheiaRouter class shown earlier
```

### aletheia/young/integration.py

Create this file with the integration code:

```python
# Insert the complete code from the YoungAletheiaIntegration class shown earlier
```

### aletheia/young/templates/young_interface.html

Create this file with the web interface template:

```html
# Insert the complete MAIN_INTERFACE_TEMPLATE shown earlier
```

### aletheia/young/templates/customization.html

Create this file with the customization interface template:

```html
# Insert the complete CUSTOMIZATION_TEMPLATE shown earlier
```

## 4. Modify Existing Files

### aletheia/config.py

Add these configuration options to the CONFIG dictionary:

```python
# === Young Aletheia ===
"YOUNG_ALETHEIA_ENABLED": os.getenv("YOUNG_ALETHEIA_ENABLED", "true").lower() == "true",
```

### aletheia/api/main.py

Modify the FastAPI initialization to include Young Aletheia:

```python
from fastapi import FastAPI
# other imports...

app = FastAPI(
    title="Aletheia API",
    description="Cognitive interface for the Aletheia self-reflective agent.",
    version="0.1.0"
)

# === CORS Configuration ===
# ... existing CORS setup ...

# === Route Registration ===
# ... existing route registration ...

# === Initialize Young Aletheia if enabled ===
if CONFIG.get("YOUNG_ALETHEIA_ENABLED", True):
    from aletheia.young import initialize_young_aletheia
    young_aletheia = initialize_young_aletheia(app)
```

## 5. Integration with Existing Code

### aletheia/main.py

Modify the main entry point to include Young Aletheia in the CLI:

```python
def main():
    """Main entry point for Aletheia"""
    parser = argparse.ArgumentParser(description="Aletheia - Self-Reflective Cognitive Agent")
    # ... existing arguments ...
    parser.add_argument("--young", action="store_true", help="Enable Young Aletheia features")
    
    args = parser.parse_args()
    
    # ... existing code ...
    
    # Run components based on arguments
    if args.all:
        # ... existing code ...
        if CONFIG.get("YOUNG_ALETHEIA_ENABLED", True):
            # Initialize Young Aletheia
            from aletheia.young import initialize_young_aletheia
            young_aletheia = initialize_young_aletheia()
    
    # ... existing code ...
    
    elif args.young:
        # Run Young Aletheia specific CLI
        print("Starting Young Aletheia CLI...")
        from aletheia.young import initialize_young_aletheia
        young_aletheia = initialize_young_aletheia()
        # Keep process running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Young Aletheia stopped by user")
```

## 6. Example .env Configuration

Add these settings to your .env file:

```
# === Young Aletheia Configuration ===
YOUNG_ALETHEIA_ENABLED=true
TELEGRAM_TOKEN=your-telegram-bot-token
CHAT_ID=your-chat-id
```

## 7. Running the Implementation

After implementing all the files, you can run Young Aletheia in several ways:

1. Start the full API server, which will include Young Aletheia:
   ```bash
   python -m aletheia.main --server
   ```

2. Start just Young Aletheia:
   ```bash
   python -m aletheia.main --young
   ```

3. Start everything including Young Aletheia:
   ```bash
   python -m aletheia.main --all
   ```

## 8. Interacting with Young Aletheia

### Web Interface
Access the web interface at: http://localhost:8000/young/

### Telegram
If properly configured, you can interact with Young Aletheia through Telegram.

### REST API
You can also interact with Young Aletheia through its REST API endpoints:
- POST /young/message - Send a message to the child
- GET /young/status - Get the child's current status
- POST /young/update - Update the child's parameters

## 9. Customizing the Persona

You can customize the child's persona through the web interface at http://localhost:8000/young/customization or by directly modifying the JSON file at `aletheia/young/data/young_aletheia_persona.json`.

## 10. Troubleshooting

### Telegram Bot Issues
- Ensure that you have a valid Telegram bot token
- Make sure the bot has been added to the chat specified by CHAT_ID
- Check logs for any errors related to Telegram API

### Web Interface Issues
- Ensure that the FastAPI server is running
- Check that the templates directory is properly set up
- Verify that static files are properly accessible

### Integration Issues
- Check that the Young Aletheia feature is enabled in your configuration
- Ensure all required dependencies are installed
- Verify that all the files are in the correct locations
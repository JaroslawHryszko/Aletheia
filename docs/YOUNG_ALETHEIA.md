# Young Aletheia Integration Guide

This guide explains how to integrate the Young Aletheia module into the main Aletheia project.

## Directory Structure

First, create the necessary directories:

```bash
mkdir -p aletheia/young_aletheia
mkdir -p aletheia/young_aletheia/data
mkdir -p aletheia/young_aletheia/templates
mkdir -p aletheia/young_aletheia/static
```

## Installation Steps

1. Copy all the Python files to the appropriate locations:
   - `young_aletheia/__init__.py`
   - `young_aletheia/persona.py`
   - `young_aletheia/developmental_model.py`
   - `young_aletheia/message_generator.py`
   - `young_aletheia/learning_engine.py`
   - `young_aletheia/telegram_bot.py`
   - `young_aletheia/interface.py`
   - `young_aletheia/integration.py`

2. Create the template directory and add the templates:
   - `young_aletheia/templates/young_interface.html`
   - `young_aletheia/templates/customization.html`

3. Create a static directory for any static assets:
   - `young_aletheia/static/` (can be populated with CSS, JS, images as needed)

## Configuration

1. Add the following to your `.env` file or `config.yaml`:

```
# Young Aletheia Configuration
YOUNG_ALETHEIA_ENABLED=true
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
```

2. Update `aletheia/config.py` to include Young Aletheia settings:

```python
# === Young Aletheia ===
"YOUNG_ALETHEIA_ENABLED": os.getenv("YOUNG_ALETHEIA_ENABLED", "true").lower() == "true",
"TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN", ""),
"CHAT_ID": os.getenv("CHAT_ID", ""),
```

## Integration with Main Application

Add the initialization code to your main FastAPI application in `aletheia/api/main.py`:

```python
from fastapi import FastAPI
# Other imports...

app = FastAPI(
    title="Aletheia API",
    description="Cognitive interface for the Aletheia self-reflective agent.",
    version="0.1.0"
)

# === CORS Configuration ===
# ...

# === Route Registration ===
# ...

# === Initialize Young Aletheia if enabled ===
if CONFIG.get("YOUNG_ALETHEIA_ENABLED", True):
    from aletheia.young_aletheia import initialize_young_aletheia
    young_aletheia = initialize_young_aletheia(app)
```

## Command-line Integration

Update `aletheia/main.py` to include the Young Aletheia command:

```python
def main():
    """Main entry point for Aletheia"""
    parser = argparse.ArgumentParser(description="Aletheia - Self-Reflective Cognitive Agent")
    # ...existing arguments...
    parser.add_argument("--young", action="store_true", help="Enable Young Aletheia features")
    
    args = parser.parse_args()
    
    # ...existing code...
    
    elif args.young:
        # Run Young Aletheia specific CLI
        print("Starting Young Aletheia CLI...")
        from aletheia.young_aletheia import initialize_young_aletheia
        young_aletheia = initialize_young_aletheia()
        # Keep process running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Young Aletheia stopped by user")
```

## Required Dependencies

Add these to your requirements.txt:

```
python-telegram-bot>=13.0
emoji>=2.0.0
jinja2>=3.0.0
```

## Running Young Aletheia

After integration, you can run Young Aletheia in several ways:

1. Start the main API server with Young Aletheia enabled:
   ```bash
   python -m aletheia.main --server
   ```

2. Start just Young Aletheia:
   ```bash
   python -m aletheia.main --young
   ```

## Accessing Young Aletheia

- Web Interface: http://localhost:8000/young/
- Customization: http://localhost:8000/young/customization
- REST API endpoints:
  - POST /young/message - Send a message to the YoungAletheia
  - GET /young/status - Get the YoungAletheia's current status
  - POST /young/update - Update the YoungAletheia's parameters
- Telegram bot (if configured)

## Troubleshooting

1. If you get an error about missing templates:
   - Ensure the templates directory is correctly located
   - Check that Jinja2 is installed

2. If the Telegram bot isn't working:
   - Verify your TELEGRAM_TOKEN and CHAT_ID are correct
   - Ensure you've added the bot to the chat specified by CHAT_ID

3. If WebSocket communication fails:
   - Check for any CORS issues
   - Ensure the WebSocket route is properly registered

4. If the static files aren't loading:
   - Verify the static directory is properly mounted

## Credits

Young Aletheia was developed as an extension to the Aletheia project, enabling it to emulate a growing human's development and interaction patterns.

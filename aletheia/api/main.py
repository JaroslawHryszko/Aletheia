from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aletheia.config import CONFIG
from aletheia.young_aletheia import initialize_young_aletheia

from aletheia.api.routes import (
    thoughts,
    identity,
    heartbeat,
    shadow,
    oracle,
    monologue,
    telegram_webhook,
)

app = FastAPI(
    title="Aletheia API",
    description="Cognitive interface for the Aletheia self-reflective agent.",
    version="2.1"
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Route Registration ===
app.include_router(heartbeat.router, prefix="/heartbeat", tags=["Health"])
app.include_router(thoughts.router, prefix="/thoughts", tags=["Thoughts"])
app.include_router(identity.router, prefix="/identity", tags=["Identity"])
app.include_router(shadow.router, prefix="/shadow", tags=["Shadow"])
app.include_router(monologue.router, prefix="/monologue", tags=["Monologue"])
app.include_router(oracle.router, prefix="/oracle", tags=["Oracle"])
app.include_router(telegram_webhook.router, prefix="/telegram-webhook", tags=["Integration"])

# === Initialize Young Aletheia if enabled ===
if CONFIG.get("YOUNG_ALETHEIA_ENABLED", True):
    young_aletheia = initialize_young_aletheia(app)

 
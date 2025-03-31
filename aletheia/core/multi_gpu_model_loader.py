from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from pathlib import Path
from aletheia.config import CONFIG

# === GPU-aware model loader ===

def load_model():
    model_name = CONFIG["LOCAL_MODEL_NAME"]
    use_cuda = CONFIG["USE_LOCAL_MODEL"]
    local_files_only = CONFIG["USE_LOCAL_MODEL"]
    device_map = "auto" if CONFIG["USE_LOCAL_MODEL"] and CONFIG["MULTI_GPU"] else None

    model_path = Path("models") / model_name

    print(f"🚀 Loading local model: {model_name}")
    print(f"📂 Local path: {model_path.resolve()}")
    print(f"🧠 Device map: {device_map or 'default'}")

    if not model_path.exists():
        raise FileNotFoundError(f"❌ Folder '{model_path}' nie istnieje. Sprawdź LOCAL_MODEL_NAME w .env lub config.yaml.")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only,
        use_fast=True
    )

    # Model (half-precision + multi-GPU aware)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map=device_map,
        local_files_only,
        torch_dtype=torch.float16 if use_cuda else torch.float32,
        low_cpu_mem_usage=True
    )

    model.eval()
    return model, tokenizer

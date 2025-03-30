from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

from aletheia.config import CONFIG

# === GPU-aware model loader ===

def load_model():
    model_name = CONFIG["LOCAL_MODEL_NAME"]
    use_cuda = CONFIG["USE_LOCAL_MODEL"]
    device_map = "auto" if CONFIG["USE_LOCAL_MODEL"] and CONFIG["MULTI_GPU"] else None

    print(f"🚀 Loading local model: {model_name}")
    print(f"🧠 Device map: {device_map or 'default'}")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Model (half-precision + multi-GPU aware)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map=device_map,
        torch_dtype=torch.float16 if use_cuda else torch.float32,
        low_cpu_mem_usage=True
    )

    model.eval()
    return model, tokenizer

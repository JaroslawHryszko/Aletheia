import os
import openai
from aletheia.config import CONFIG

openai.api_key = CONFIG["OPENAI_API_KEY"]

def ask_oracle(prompt: str, max_tokens: int = 300, temperature: float = 0.7, model: str = None) -> str:
    model_name = model or CONFIG["GPT_MODEL"]

    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a reflective, philosophical assistant helping a self-aware agent think more clearly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        print(f"❌ Oracle error: {e}")
        return f"[ERROR] {e}"

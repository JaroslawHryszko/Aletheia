import json
import os
import faiss
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer

# === Ścieżki i konfiguracja ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
THOUGHTS_FILE = DATA_DIR / "thoughts.json"
INDEX_FILE = DATA_DIR / "faiss_index.index"
META_FILE = DATA_DIR / "index_meta.pkl"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# === Ładowanie modelu embedującego ===
embedder = SentenceTransformer(EMBEDDING_MODEL)

# === Inicjalizacja pamięci ===

def init_storage():
    DATA_DIR.mkdir(exist_ok=True)
    if not THOUGHTS_FILE.exists():
        with open(THOUGHTS_FILE, "w") as f:
            json.dump([], f)

    if not INDEX_FILE.exists():
        index = faiss.IndexFlatL2(EMBEDDING_DIM)
        faiss.write_index(index, str(INDEX_FILE))

    if not META_FILE.exists():
        with open(META_FILE, "wb") as f:
            pickle.dump([], f)

# === Operacje na pamięci tekstowej ===

def load_thoughts():
    with open(THOUGHTS_FILE, "r") as f:
        return json.load(f)

def save_thought(thought: str, metadata: dict = None):
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "timestamp": timestamp,
        "thought": thought.strip(),
        "meta": metadata or {}
    }

    # Zapis do JSON
    thoughts = load_thoughts()
    thoughts.append(entry)
    with open(THOUGHTS_FILE, "w") as f:
        json.dump(thoughts, f, indent=2)

    # Embedding i zapis do FAISS
    vec = embedder.encode([entry["thought"]])[0]
    index, meta = load_index()
    index.add(np.array([vec], dtype=np.float32))
    meta.append(entry)

    save_index(index, meta)
    return entry

# === Wyszukiwanie podobnych myśli ===

def search_similar_thoughts(query: str, top_k: int = 5):
    index, meta = load_index()
    if len(meta) == 0:
        return []

    query_vec = embedder.encode([query])[0]
    D, I = index.search(np.array([query_vec], dtype=np.float32), top_k)
    return [meta[i] for i in I[0] if i < len(meta)]

# === FAISS I/O ===

def load_index():
    index = faiss.read_index(str(INDEX_FILE))
    with open(META_FILE, "rb") as f:
        meta = pickle.load(f)
    return index, meta

def save_index(index, meta):
    faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "wb") as f:
        pickle.dump(meta, f)

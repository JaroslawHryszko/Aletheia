import json
from pathlib import Path

def safe_create_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def read_json(file_path: Path, default=None):
    if not file_path.exists():
        return default
    with open(file_path, "r") as f:
        return json.load(f)

def write_json(file_path: Path, data: dict):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

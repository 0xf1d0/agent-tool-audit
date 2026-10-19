"""Small dependency-free serialization and provenance helpers."""
import hashlib
import json
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def lines(path):
    for n, text in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if text.strip():
            try:
                yield json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {n} in {path}") from exc

def jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")

def fresh(path):
    path = Path(path)
    if path.exists():
        raise ValueError(f"Output already exists: {path}; use a new experiment directory")
    path.mkdir(parents=True)
    return path

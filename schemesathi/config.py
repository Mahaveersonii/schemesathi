"""Settings, read from .env (copy .env.example to .env and add your free Groq key)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
SCHEMES_DIR = DATA / "schemes"
CHROMA_DIR = DATA / "chroma"
LOG_DB = DATA / "schemesathi.db"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
MODELS = [m.strip() for m in os.getenv(
    "MODELS", "groq/openai/gpt-oss-120b,groq/openai/gpt-oss-20b,groq/qwen/qwen3.8-27b").split(",") if m.strip()]

CHUNK_CHARS, OVERLAP_CHARS = 900, 150
ALPHA = 0.9          # blend: 0.9 x meaning similarity + 0.1 x keyword overlap (tuned in eval/run_eval.py)

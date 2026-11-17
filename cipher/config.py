import os
from pathlib import Path

DATA_DIR = Path.home() / ".cipher"
DATA_DIR.mkdir(parents=True, exist_ok=True)
API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
MAX_HISTORY = 30

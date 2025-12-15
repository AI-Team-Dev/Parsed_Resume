import os
from pathlib import Path

# Get the project root directory (parent of backend folder)
BASE_DIR = Path(__file__).parent.parent

# Grok API Configuration
# Load from environment variable (required for production/hosting)
# For local development, create a .env file with your API keys
ENV_API_KEYS = os.getenv("GROK_API_KEYS", "")
if ENV_API_KEYS:
    # Split comma-separated keys from environment variable
    GROK_API_KEYS = [key.strip() for key in ENV_API_KEYS.split(",") if key.strip()]
else:
    # No API keys found - user must set GROK_API_KEYS environment variable
    GROK_API_KEYS = []
    print("[WARNING] No GROK_API_KEYS environment variable found. Please set it in .env file or environment variables.")

GROK_API_KEY = GROK_API_KEYS[0] if GROK_API_KEYS else ""
GROK_URL = os.getenv("GROK_URL", "https://api.x.ai/v1/chat/completions")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-fast-reasoning")
MAX_WORKERS = min(8, len(GROK_API_KEYS) * 4) if GROK_API_KEYS else 1
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

# Load prompt from file (in project root)
PROMPT_PATH = BASE_DIR / "grok_resume_prompt.txt"

try:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        PROMPT = f.read()
    print(f"[INFO] Loaded prompt from: {PROMPT_PATH}")
except FileNotFoundError:
    print(f"[WARNING] Prompt file not found at: {PROMPT_PATH}")
    # Fallback prompt
    PROMPT = """You are an expert resume parser. Extract the following information from the resume text and return it as a JSON object:
- Name
- Email
- Phone
- Skills
- Experience
- Education
- Summary

Return only valid JSON without any additional text or markdown formatting."""

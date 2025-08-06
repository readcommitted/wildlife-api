"""
settings.py - Central configuration for Wildlife Image Processing & Semantic Search System

All file system paths are derived from MEDIA_ROOT to ensure consistent structure.
Secrets (API keys, tokens) reside in secrets.toml for Streamlit.
"""

import os
from pathlib import Path



# --- Helper Functions ---
def normalize_root(env_var: str, default: str) -> Path:
    """
    Resolve a filesystem path from an environment variable, falling back to a default.
    """
    raw = os.getenv(env_var, default)
    if not (raw.startswith(os.sep) or raw.startswith('.') or raw.startswith('~')):
        raw = os.sep + raw
    return Path(raw).expanduser().resolve()


# --- Secrets & User-Agent ---
try:
    DATABASE_URL = os.getenv("DATABASE_URL", None)

except ImportError:
    OPENAI_API_KEY = None


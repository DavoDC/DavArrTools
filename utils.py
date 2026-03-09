"""
utils.py — Shared helpers for DavArrTools scripts.
"""

import logging
import os
import subprocess
import sys
from datetime import datetime

LOG_DIR = "logs"


def ensure_requirements():
    """Auto-install missing packages from requirements.txt if needed."""
    try:
        import requests
    except ImportError:
        print("Missing required packages. Installing from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Done.\n")


def setup_logging(script_name: str) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    return log_file


def fetch_arr_data(base_url: str, api_key: str, endpoint: str) -> list[dict]:
    """Generic GET to an arr API endpoint. Returns parsed JSON list."""
    import requests
    url = f"{base_url.rstrip('/')}/api/v3/{endpoint}"
    headers = {"X-Api-Key": api_key}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

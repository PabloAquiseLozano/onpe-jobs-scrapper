import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

SCRAPE_INTERVAL_HOURS = 4.8
DAILY_SCRAPES = 5

CHROME_PATH = shutil.which("google-chrome-stable") or shutil.which("google-chrome") or "/usr/bin/google-chrome-stable"

ONPE = {
    "name": "ONPE",
    "base_url": "https://reclutamiento.onpe.gob.pe/convocatorias",
    "chrome_path": CHROME_PATH,
    "cf_wait": 20,
    "headless": True,
}

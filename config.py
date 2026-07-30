import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

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

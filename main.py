import schedule
import sys
from datetime import datetime

from config import ONPE, DATA_DIR, SCRAPE_INTERVAL_HOURS
from scraper.onpe_scraper import ONPEScraper


def scrape_onpe():
    print(f"[{datetime.now().isoformat()}] Scraping ONPE...")
    scraper = ONPEScraper(ONPE, DATA_DIR)
    try:
        data = scraper.scrape()
        filepath = scraper.save_json(data)
        print(f"  -> {len(data)} convocatorias guardadas en {filepath}")
    except Exception as e:
        print(f"  -> Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(scrape_onpe)
        print(f"Scheduler iniciado. Scraping cada {SCRAPE_INTERVAL_HOURS} horas.")
        scrape_onpe()
        while True:
            schedule.run_pending()
            import time
            time.sleep(60)
    else:
        scrape_onpe()

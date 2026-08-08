from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path

from database.supabase_client import upsert_convocatorias


class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def save_to_db(self, data: list[dict]) -> dict[str, int]:
        return upsert_convocatorias(data)

    def save_json(self, data: list[dict], filename: str | None = None):
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = filename or f"{self.config['name']}_{date_str}.json"

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        filepath = data_dir / filename
        output = {
            "source": self.config["name"],
            "scraped_at": datetime.now().isoformat(),
            "count": len(data),
            "data": data,
        }
        filepath.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        return filepath

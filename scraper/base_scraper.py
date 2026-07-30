from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path


class BaseScraper(ABC):
    def __init__(self, config: dict, data_dir: Path):
        self.config = config
        self.data_dir = data_dir

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def save_json(self, data: list[dict], filename: str | None = None):
        if filename is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{self.config['name']}_{date_str}.json"

        filepath = self.data_dir / filename
        output = {
            "source": self.config["name"],
            "scraped_at": datetime.now().isoformat(),
            "count": len(data),
            "data": data,
        }
        filepath.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        return filepath

import csv
from pathlib import Path

from backend.app.connectors.base import DataConnector


class CsvConnector(DataConnector):
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def fetch_rows(self) -> list[dict[str, str]]:
        with self.file_path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

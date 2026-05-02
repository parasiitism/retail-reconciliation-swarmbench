from abc import ABC, abstractmethod


class DataConnector(ABC):
    @abstractmethod
    def fetch_rows(self) -> list[dict[str, str]]:
        pass

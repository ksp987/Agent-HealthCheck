from abc import ABC, abstractmethod
from typing import Dict, List

class StoreResultsPort(ABC):
    @abstractmethod
    def save_results(self, results: List[Dict]) -> None:
        """
        Store the given results in a persistent storage.
        Each result will have id, subject, from, date, insights.
        """
        pass
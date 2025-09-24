# src/core/ports/email_port.py

from abc import ABC, abstractmethod
from typing import List, Dict

class GetEmailPort(ABC):
    @abstractmethod
    def fetch_emails(self, subject: str, minutes: int) -> List[Dict]:
        """
        Retrieve a list of emails for a given user.
        Returns a list of dictionaries with parsed email metadata + insights.
        """
        pass
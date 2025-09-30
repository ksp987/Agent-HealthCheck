# src/adapters/gmail_adapter.py

import logging
from datetime import datetime, timedelta
from pytz import timezone

from src.core.ports.email_port import GetEmailPort
from src.infrastructure.gmail_service import GmailService
from src.infrastructure.email_processor import EmailProcessor

logger = logging.getLogger(__name__)


class GmailAdapter(GetEmailPort):
    """
    Adapter that implements GetEmailPort.
    Delegates Gmail + OpenAI work to the infrastructure EmailProcessor.
    """

    def __init__(self, credentials_env: str, delegated_user_env: str, tz_name: str = "Australia/Melbourne", processor=None):
        gmail = GmailService(credentials_env, delegated_user_env)

        # Use injected processor if provided (for testing)
        self.processor = processor or EmailProcessor(gmail.get_service())
        self.tz = timezone(tz_name)

    def fetch_emails(self, subject: str, minutes: int):
        """
        Fetch emails by subject within the last X minutes.
        Returns list of dicts with {id, subject, from, date, insights}.
        """
        now = datetime.now(self.tz)
        cutoff_time = now - timedelta(minutes=minutes)
        epoch_time = int(cutoff_time.timestamp())

        results = self.processor.process_recent_messages(minutes, subject=subject)
        logger.info(
            "Adapter fetched %d emails with subject '%s' since %s",
            len(results), subject, cutoff_time.isoformat()
        )
        return results

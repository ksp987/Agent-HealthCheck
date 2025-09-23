#src/adapters/gmail_adapter.py

import logging
from datetime import datetime, timedelta
from pytz import timezone

from src.core.ports.email_port import GetEmailPort
from src.infrastructure.gmail_service import GmailService
from src.infrastructure.email_processor import EmailProcessor

logger = logging.getLogger(__name__)

class GmailAdapter(GetEmailPort):
    def __init__(self, credentials_env: str, delegated_user_env: str, tz_name="Australia/Melbourne"):
        gmail = GmailService(credentials_env, delegated_user_env)
        self.processor = EmailProcessor(gmail.get_service())
        self.tz = timezone(tz_name)

    def fetch_emails(self, subject: str, minutes: int):
        # Calculate cutoff time
        now = datetime.now(self.tz)
        cutoff_time = now - timedelta(minutes=minutes)
        epoch_time = int(cutoff_time.timestamp())

        # Use EmailProcessor to get structured messages
        results = self.processor.process_recent_messages(minutes, subject=subject)

        logger.info(f"Fetched {len(results)} emails with subject '{subject}' in last {minutes} minutes.")
        return results

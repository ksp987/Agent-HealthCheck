# src/ai_agent/gmail_service.py

import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GmailService:
    """
    Handles authentication and returns an authorized Gmail API client.
    """

    def __init__(self, credentials_path_env: str, delegated_user_env: str, scopes=None):
        self.credentials_path = os.getenv(credentials_path_env)
        self.delegated_user = os.getenv(delegated_user_env)
        self.scopes = scopes or ["https://www.googleapis.com/auth/gmail.readonly"]
        self.service = self._initialize_service()

    def _initialize_service(self):
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise FileNotFoundError("Service account JSON file not found or invalid.")

        logger.info("Loading Gmail service account credentials...")

        try:
            with open(self.credentials_path, "r") as f:
                service_account_info = json.load(f)
        except Exception as e:
            raise ValueError("Failed to read Gmail service account JSON file") from e

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=self.scopes
        )

        delegated_credentials = credentials.with_subject(self.delegated_user)

        try:
            logger.info("Building Gmail API client...")
            return build("gmail", "v1", credentials=delegated_credentials)
        except Exception as e:
            raise RuntimeError("Failed to initialize Gmail API client") from e

    def get_service(self):
        return self.service


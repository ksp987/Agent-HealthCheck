# src/ai_agent/gmail_reader.py

import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scope
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# STEP 1: Load path to service account JSON from environment
cred_file_path = os.getenv("GMAIL_SERVICE_ACCOUNT_JSON")

if not cred_file_path or not os.path.exists(cred_file_path):
    raise EnvironmentError("GMAIL_SERVICE_ACCOUNT_JSON path not found or invalid")

logger.info("Loaded Gmail credentials file path from environment")

# STEP 2: Read and parse the JSON file
try:
    with open(cred_file_path, "r") as f:
        service_account_info = json.load(f)
except Exception as e:
    raise ValueError("Failed to read or parse Gmail service account JSON file") from e

# STEP 3: Create service account credentials
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

# Onsys support email access
delegated_credentials = credentials.with_subject("support@onsys.com.au")
service = build("gmail", "v1", credentials=delegated_credentials)


# STEP 4: Build the Gmail API client
try:
    service = build("gmail", "v1", credentials=delegated_credentials)
    logger.info("Gmail API client initialized successfully")
except Exception as e:
    raise RuntimeError("Failed to initialize Gmail API client") from e

# STEP 5: Sample test – List latest emails
def list_emails():
    try:
        response = service.users().messages().list(userId='me', maxResults=20).execute()
        messages = response.get('messages', [])
        for msg in messages:
            logger.info(f"Email ID: {msg['id']}")
    except Exception as e:
        logger.error(f"Failed to fetch emails: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Gmail healthcheck email reader...")
    list_emails()
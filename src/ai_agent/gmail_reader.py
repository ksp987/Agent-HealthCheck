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

# STEP 1: Load service account credentials (from GitHub Secret or .env)
cred_json_str = os.getenv("GMAIL_SERVICE_ACCOUNT_JSON")

if not cred_json_str:
    raise EnvironmentError("GMAIL_SERVICE_ACCOUNT_JSON not found in environment variables")

logger.info("Loaded Gmail credentials from environment")

# STEP 2: Parse the JSON string into a Python dict
try:
    service_account_info = json.loads(cred_json_str)
except json.JSONDecodeError as e:
    raise ValueError("Invalid JSON in Gmail credentials") from e

# STEP 3: Create service account credentials with delegated user
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

# # If you want to impersonate support@onsys.com.au
# delegated_credentials = credentials.with_subject("support@onsys.com.au")

# STEP 4: Build the Gmail API client
try:
    service = build("gmail", "v1", credentials=delegated_credentials)
    logger.info("Gmail API client initialized successfully")
except Exception as e:
    raise RuntimeError("Failed to initialize Gmail API client") from e

# STEP 5: Sample test – List latest emails
def list_emails():
    try:
        response = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = response.get('messages', [])
        for msg in messages:
            logger.info(f"Email ID: {msg['id']}")
    except Exception as e:
        logger.error(f"Failed to fetch emails: {str(e)}")

if __name__ == "__main__":
    logger.info( "Starting Gmail healthcheck email reader...")
    list_emails()

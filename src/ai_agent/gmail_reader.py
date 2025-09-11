# src/ai_agent/gmail_reader.py

import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pytz import timezone
from datetime import datetime, timedelta
from pytz import timezone

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
        # Calculate the timestamp for 15 minutes ago in Melbourne timezone
        melbourne_tz = timezone('Australia/Melbourne')
        now_melbourne = datetime.now(melbourne_tz)
        fifteen_minutes_ago = now_melbourne - timedelta(minutes=15)
        epoch_time = int(fifteen_minutes_ago.timestamp())
        # Gmail query to find emails after the calculated time with specific subject
        query = f"after:{epoch_time} subject:'Health Check Report'"
        user_id = 'me'
        emails = []
        next_page_token = None
        while True:
            response = service.users().messages().list(userId=user_id, 
                                                       q=query, 
                                                       pageToken=next_page_token).execute()
            messages = response.get('messages', [])
            emails.extend(messages)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        logger.info(f"Fetched {len(emails)} emails matching the criteria.")
        for msg in emails:
            logger.info(f"Email ID: {msg['id']}")

    except Exception as e:
        logger.error(f"Failed to fetch emails: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Gmail healthcheck email reader...")
    list_emails()
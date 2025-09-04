# src/ai_agents/gmail_reader.py

import os
import base64
import mimetypes
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = os.path.join(os.path.dirname(__file__), '../../secrets/token.json')

ATTACHMENTS_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')  # store attachments here
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

def read_healthcheck_attachments():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', q='subject:HealthCheck has:attachment', maxResults=5).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No HealthCheck emails with attachments found.")
        return

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        parts = msg_data['payload'].get('parts', [])

        for part in parts:
            filename = part.get("filename")
            body = part.get("body", {})
            att_id = body.get("attachmentId")

            if att_id and filename:
                attachment = service.users().messages().attachments().get(
                    userId='me',
                    messageId=msg['id'],
                    id=att_id
                ).execute()

                data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))

                filepath = os.path.join(ATTACHMENTS_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(data)
                print(f"Downloaded attachment: {filename}")

if __name__ == "__main__":
    read_healthcheck_attachments()

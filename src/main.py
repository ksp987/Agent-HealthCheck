#src/main.py

from src.ai_agent.gmail_service import GmailService
from src.ai_agent.email_fetcher import EmailFetcher

def main():
    gmail = GmailService("GMAIL_SERVICE_ACCOUNT_JSON", "GMAIL_DELEGATED_USER")
    fetcher = EmailFetcher(gmail.service)

    # Fetch emails from the last 15 minutes with a specific subject
    msgs = fetcher.list_messages_since(minutes=15, subject="Health Check Report")
    for msg in msgs:
        meta = fetcher.get_message(msg['id'], fmt='metadata')
        print(meta)

if __name__ == "__main__":
    main()

from src.ai_agent.gmail_service import GmailService
from src.ai_agent.email_processor import EmailProcessor

def main():
    gmail = GmailService("GMAIL_SERVICE_ACCOUNT_JSON", "GMAIL_DELEGATED_USER")
    processor = EmailProcessor(gmail.service)

    results = processor.process_recent_messages(60, subject="Health Check Report")
    print(results)   

if __name__ == "__main__":
    main()

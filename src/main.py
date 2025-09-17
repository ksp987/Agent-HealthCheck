from src.ai_agent.gmail_service import GmailService
from src.ai_agent.email_processor import EmailProcessor
from src.ai_agent.parameter_engine import ParameterEngine

def main():
    gmail = GmailService("GMAIL_SERVICE_ACCOUNT_JSON", "GMAIL_DELEGATED_USER")
    processor = EmailProcessor(gmail.service)

    results = processor.process_recent_messages(90, subject="Health Check Report")
    
    for msg in results:
        print("\n Message ID:", msg["id"])
        insights = msg["insights"]

        engine = ParameterEngine(insights)
        evaluation = engine.evaluate()

        # print(" Raw Insights:", insights)
        print(" Evaluation:", evaluation)


if __name__ == "__main__":
    main()

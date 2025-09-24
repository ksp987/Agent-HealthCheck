# src/main.py

import logging
from src.adapters.gmail_adapter import GmailAdapter
from src.core.parameter_engine import ParameterEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Use adapter (implements GetEmailPort)
    adapter = GmailAdapter("GMAIL_SERVICE_ACCOUNT_JSON", "GMAIL_DELEGATED_USER")

    # Fetch emails (with metadata + insights)
    results = adapter.fetch_emails("Health Check Report", 90)

    for msg in results:
        print("\nMessage ID:", msg["id"])
        print("From:", msg.get("from"))
        print("Date:", msg.get("date"))
        print("Subject:", msg.get("subject"))
        print("Raw Insights:", msg["insights"])

        # Evaluate insights with ParameterEngine
        engine = ParameterEngine(msg["insights"])
        evaluation = engine.evaluate()
        print("Evaluation:", evaluation)


if __name__ == "__main__":
    main()

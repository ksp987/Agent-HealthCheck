# src/main.py

import logging
from src.adapters.gmail_adapter import GmailAdapter
from src.adapters.postgres_adapter import PostgresAdapter
from src.core.parameter_engine import ParameterEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Use adapter (implements GetEmailPort)
    email_adapter = GmailAdapter("GMAIL_SERVICE_ACCOUNT_JSON", "GMAIL_DELEGATED_USER")
    # storage_adapter = PostgresAdapter("AZURE_SQL_CONN")

    # Fetch emails (with metadata + insights)
    results = email_adapter.fetch_emails("Health Check Report", 180)

    
    for report in results:  # report is a HealthCheckReport
        print("\nMessage ID:", report.message_id)
        print("From:", report.sender)
        print("Date:", report.date)
        print("Subject:", report.subject)
        print("Host:", report.host)
        print("SQL Services:", [s.name for s in report.services])
        print("Disk Usage:", [(d.drive, d.free_percent) for d in report.disks])

        # Evaluate insights with ParameterEngine
        engine = ParameterEngine(report)
        evaluation = engine.evaluate()

        print("Final Severity:", evaluation.severity)
        for alert in evaluation.alerts:
            print(f"- [{alert.level.upper()}] {alert.message}")

if __name__ == "__main__":
    main()

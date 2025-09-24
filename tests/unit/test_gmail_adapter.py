# tests/unit/test_gmail_adapter.py

import pytest
from src.adapters.gmail_adapter import GmailAdapter

class DummyProcessor:
    def process_recent_messages(self, minutes, subject):
        return [
            {
                "id": "123",
                "subject": subject,
                "from": "monitor@company.com",
                "date": "Thu, 25 Sep 2025 07:00:00 +1000",
                "insights": {"cpu": "ok"},
            }
        ]

class DummyGmailService:
    def get_service(self):
        return "fake-service"


def test_fetch_emails_returns_metadata_and_insights(monkeypatch):
    # Patch GmailService used inside GmailAdapter
    monkeypatch.setattr("src.adapters.gmail_adapter.GmailService", lambda c, d: DummyGmailService())

    # Now GmailAdapter won't touch real Gmail
    adapter = GmailAdapter("CRED_ENV", "USER_ENV")

    # Replace real processor with dummy
    adapter.processor = DummyProcessor()

    results = adapter.fetch_emails("Health Check Report", 30)

    assert len(results) == 1
    email = results[0]
    assert email["id"] == "123"
    assert email["subject"] == "Health Check Report"
    assert email["insights"]["cpu"] == "ok"

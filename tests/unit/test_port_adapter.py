# tests/unit/test_port_adapter.py

import pytest
from src.adapters.gmail_adapter import GmailAdapter
from src.core.ports.email_port import GetEmailPort

# Dummy infrastructure pieces
class DummyEmailProcessor:
    def process_recent_messages(self, minutes, subject):
        return [
            {
                "id": "abc123",
                "subject": subject,
                "from": "db-monitor@company.com",
                "date": "Thu, 25 Sep 2025 08:00:00 +1000",
                "insights": {"disk_usage": "healthy", "cpu": "ok"},
            }
        ]

class DummyGmailService:
    def get_service(self):
        return "fake-gmail-service"


def test_adapter_implements_port(monkeypatch):
    # Patch GmailService to avoid real Gmail API
    monkeypatch.setattr("src.adapters.gmail_adapter.GmailService", lambda c, d: DummyGmailService())

    # Construct adapter
    adapter: GetEmailPort = GmailAdapter("CRED_ENV", "USER_ENV")
    adapter.processor = DummyEmailProcessor()  # swap in fake processor

    # Exercise the port method
    results = adapter.fetch_emails("Health Check Report", 15)

    # Assertions
    assert isinstance(results, list)
    assert len(results) == 1
    email = results[0]

    assert email["id"] == "abc123"
    assert email["subject"] == "Health Check Report"
    assert email["insights"]["cpu"] == "ok"
    assert "from" in email
    assert "date" in email

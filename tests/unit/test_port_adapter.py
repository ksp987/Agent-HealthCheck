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
@pytest.mark.unit
def test_adapter_implements_port():
    # Inject DummyProcessor so no real Gmail/OpenAI is touched
    adapter: GetEmailPort = GmailAdapter("CRED_ENV", "USER_ENV", processor=DummyEmailProcessor())
    
    # Exercise the port method
    results = adapter.fetch_emails("Health Check Report", 30)

    # Assertions
    assert isinstance(results, list)
    assert len(results) == 1
    email = results[0]

    assert email["id"] == "abc123"
    assert email["subject"] == "Health Check Report"
    assert email["insights"]["cpu"] == "ok"
    assert "from" in email
    assert "date" in email

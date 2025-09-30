# tests/integration/test_gmail_adapter_integration.py

import pytest
from src.adapters.gmail_adapter import GmailAdapter
from src.core.ports.email_port import GetEmailPort

@pytest.mark.integration
def test_fetch_emails_real():
    """
    Integration test for GmailAdapter with real GmailService and EmailProcessor.
    Requires valid credentials in environment variables.
    """
    adapter: GetEmailPort = GmailAdapter("GMAIL_SERVICE_ACCOUNT_JSON", "GMAIL_DELEGATED_USER")

    results = adapter.fetch_emails("Health Check Report", 60)

    assert isinstance(results, list)

    if results: # only check contents if we got results
        email = results[0]
        assert "id" in email
        assert "subject" in email
        assert "from" in email
        assert "date" in email
        assert "insights" in email
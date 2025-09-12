import pytest
from unittest.mock import patch, MagicMock
from src.ai_agent.gmail_service import GmailService

@patch("src.ai_agent.gmail_service.build")
def test_initialize_service(mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    gmail = GmailService("GMAIL_CREDENTIALS_PATH", "GMAIL_DELEGATED_USER")

    assert gmail.get_service() == mock_service

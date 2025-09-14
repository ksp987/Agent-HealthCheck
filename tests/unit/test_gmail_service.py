from unittest.mock import patch, MagicMock, mock_open
import json
import pytest
from src.ai_agent.gmail_service import GmailService

@patch("src.ai_agent.gmail_service.build")
@patch("src.ai_agent.gmail_service.service_account.Credentials.from_service_account_info")
@patch("src.ai_agent.gmail_service.open", new_callable=mock_open, read_data=json.dumps({
    "type": "service_account",
    "project_id": "dummy",
    "private_key_id": "dummy",
    "private_key": "-----BEGIN PRIVATE KEY-----\nFAKE\n-----END PRIVATE KEY-----\n",
    "client_email": "fake-service-account@dummy.iam.gserviceaccount.com",
    "client_id": "1234567890",
    "token_uri": "https://oauth2.googleapis.com/token"
}))
@patch("src.ai_agent.gmail_service.os.path.exists", return_value=True)
@patch("src.ai_agent.gmail_service.os.getenv", side_effect=lambda key: {
    "GMAIL_CREDENTIALS_PATH": "secrets/fake.json",
    "GMAIL_DELEGATED_USER": "test@dummy.com"
}[key])
def test_initialize_service(mock_getenv, mock_exists, mock_file, mock_creds, mock_build):
    # Arrange
    mock_creds.return_value = MagicMock()   # avoids parsing private key
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Act
    gmail = GmailService("GMAIL_CREDENTIALS_PATH", "GMAIL_DELEGATED_USER")

    # Assert
    assert gmail.service == mock_service
    mock_build.assert_called_once()

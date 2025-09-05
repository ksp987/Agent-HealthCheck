#tests/test_gmail_reader.py
import os
import base64
import shutil
from unittest.mock import patch, MagicMock
from ai_agent import gmail_reader

RAW_DIR = os.path.join(os.path.dirname(__file__), '../data/raw')
TEST_FILENAME = "SQL Server Daily Health Check Report.pdf"

@patch("ai_agent.gmail_reader.Credentials")
@patch("ai_agent.gmail_reader.build")

def test_read_healthcheck_attachments(mock_build, mock_credentials):
    # Setup: clean data/raw directory
    if os.path.exists(os.path.join(RAW_DIR, TEST_FILENAME)):
        os.remove(os.path.join(RAW_DIR, TEST_FILENAME))

    # Fake Gmail API structure
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # 1 fake message returned
    mock_service.users().messages().list().execute.return_value = {
        'messages': [{'id': '123'}]
    }

    # Email content with attachment
    mock_service.users().messages().get().execute.return_value = {
        'payload': {
            'parts': [
                {
                    'filename': TEST_FILENAME,
                    'body': {'attachmentId': 'abc123'}
                }
            ]
        }
    }

    # Fake base64 attachment content
    fake_file_data = base64.urlsafe_b64encode(b"This is a test file").decode('utf-8')
    mock_service.users().messages().attachments().get().execute.return_value = {
        'data': fake_file_data
    }

    # Run the reader function
    gmail_reader.read_healthcheck_attachments()

    # Check if file was saved
    saved_file = os.path.join(RAW_DIR, TEST_FILENAME)
    assert os.path.exists(saved_file)

    # Clean up after test
    os.remove(saved_file)

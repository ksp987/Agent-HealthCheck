# tests/conftest.py
import pytest
from dotenv import load_dotenv

@pytest.fixture(autouse=True, scope="session")
def load_env():
    load_dotenv()  # loads .env automatically for all tests

@pytest.fixture(autouse=True)
def fake_openai_client(mocker):
    mocker.patch("src.infrastructure.email_processor.OpenAI", autospec=True)

# tests/conftest.py
import pytest
from dotenv import load_dotenv

@pytest.fixture(autouse=True, scope="session")
def load_env():
    load_dotenv()  # loads .env automatically for all tests

#tests/unit/test_email_processor.py

import pytest
from datetime import datetime
from src.infrastructure.email_processor import EmailProcessor

@pytest.mark.unit
def test_epoch_seconds_now_minus():
    processor = EmailProcessor(service=None)
    seconds_10_min_ago = processor._epoch_seconds_now_minus(10)
    now = int(datetime.now().timestamp())
    assert now - seconds_10_min_ago >= 600  # At least 10 minutes ago

@pytest.mark.unit
def test_build_query():
    processor = EmailProcessor(service=None)
    query = processor._build_query(1700000000, "Health Check Report")
    assert query == 'after:1700000000 subject:"Health Check Report"'

@pytest.mark.unit
def test_find_recent_messages(mocker):
    mock_service = mocker.MagicMock()
    mock_users = mock_service.users.return_value
    mock_messages = mock_users.messages.return_value
    mock_list = mock_messages.list.return_value
    mock_list.execute.return_value = {
        'messages': [{'id': '123', 'threadId': 'abc'}, {'id': '456', 'threadId': 'def'}]
    }

    processor = EmailProcessor(service=mock_service)
    results = processor.find_recent_messages(10, "Health Check Report", max_results=2)

    assert len(results) == 2
    assert results[0]['id'] == '123'
    assert results[1]['id'] == '456'
    mock_messages.list.assert_called_once()
    mock_list.execute.assert_called_once()

@pytest.mark.unit
def test_fetch_message_body(mocker):
    mock_service = mocker.MagicMock()
    mock_users = mock_service.users.return_value
    mock_messages = mock_users.messages.return_value
    mock_get = mock_messages.get.return_value
    mock_get.execute.return_value = {
        'payload': {
            'body': {'data': 'SGVsbG8gd29ybGQ='}  # "Hello world" in base64
        }
    }

    processor = EmailProcessor(service=mock_service)
    body = processor.fetch_message_body('123', prefer_html=False)

    assert body == 'Hello world'
    mock_messages.get.assert_called_once_with(userId=processor.user_id, id='123', format='full')
    mock_get.execute.assert_called_once()

@pytest.mark.unit
def test_fetch_message_metadata(mocker):
    mock_service = mocker.MagicMock()
    mock_users = mock_service.users.return_value
    mock_messages = mock_users.messages.return_value
    mock_get = mock_messages.get.return_value
    mock_get.execute.return_value = {
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Health Check Report'},
                {'name': 'From', 'value': 'admin@test.com.au'},
                {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'}
            ]                
        }
    }
    processor = EmailProcessor(service=mock_service)
    metadata = processor.fetch_message_metadata('123')
    assert metadata['subject'] == 'Health Check Report'
    assert metadata['from'] == 'admin@test.com.au'
    assert metadata['date'] == 'Mon, 1 Jan 2024 12:00:00 +0000'
    assert mock_messages.get.call_count == 1
    
@pytest.mark.unit
def test_extract_insights(mocker):
    mock_service = mocker.MagicMock()
    processor = EmailProcessor(service=mock_service)

    # Fake OpenAI response JSON
    fake_json = '{"alerts": [], "cpu": {}, "disk_usage": []}'

    # Patch completions.create to return our fake response
    mocker.patch.object(
        processor.client.chat.completions,
        "create",
        return_value=mocker.MagicMock(
            choices=[mocker.MagicMock(
                message=mocker.MagicMock(content=fake_json)
            )]
        )
    )
    body = "Sample email body for insights extraction."
    insights = processor.extract_insights(body)
    assert 'alerts' in insights
    assert isinstance(insights['alerts'], list)
    assert 'cpu' in insights
    assert 'disk_usage' in insights

@pytest.mark.unit
def test_process_recent_messages(mocker):
    mock_service = mocker.MagicMock()
    processor = EmailProcessor(service=mock_service)

    # Mock Gmail steps
    mocker.patch.object(processor, "find_recent_messages", return_value=[
        {"id": "123", "threadId": "abc"},
        {"id": "456", "threadId": "def"},
    ])
    mocker.patch.object(processor, "fetch_message_body", return_value="Email body")
    mocker.patch.object(processor, "fetch_message_metadata", return_value={
        "subject": "Health Check Report",
        "from": "admin@test.com.au",
        "date": "Mon, 1 Jan 2024 12:00:00 +0000"
    })

    # Mock OpenAI insights → minimal structure for mapper
    mocker.patch.object(processor, "extract_insights", return_value={
        "host": "test-server",
        "sql_services": [
            {"name": "MSSQLSERVER", "display_name": "SQL Server", "status": "Running"}
        ],
        "disk_usage": [
            {"drive": "C:", "total_gb": 100, "free_gb": 50, "free_percent": 50}
        ],
        "cpu": {
            "samples": [{"timestamp": "2024-01-01T00:00:00", "percent": 20.5}],
            "top_db_usage": []
        },
        "memory": {
            "available_mb": 8000,
            "available_percent": 40,
            "physical_gb": 16,
            "buffer_top_db": []
        },
        "backups": {
            "databases_offline": [],
            "databases_missing_log_backup": [],
            "note": "All good"
        },
        "failed_jobs": [],
        "alerts": []   # this will be mapped into Evaluation
    })

    # Run the pipeline
    results = processor.process_recent_messages(10, "Health Check Report")

    # Assertions
    assert len(results) == 2
    report = results[0]
    assert report.message_id == "123"
    assert report.subject == "Health Check Report"
    assert report.sender == "admin@test.com.au"
    assert report.host == "test-server"

    # Check that typed fields were built correctly
    assert isinstance(report.services[0], type(results[0].services[0]))  # SqlService
    assert isinstance(report.disks[0], type(results[0].disks[0]))        # DiskUsage
    assert isinstance(report.cpu, type(results[0].cpu))                  # CpuUsage
    assert isinstance(report.memory, type(results[0].memory))            # MemoryUsage
    assert isinstance(report.backups, type(results[0].backups))          # BackupStatus
    assert isinstance(report.evaluation, type(results[0].evaluation))    # Evaluation

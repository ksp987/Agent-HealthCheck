# tests/unit/test_mappers.py

import pytest
from datetime import datetime
from src.core import mappers
from src.core.models import SqlService, DiskUsage, CpuUsage, MemoryUsage, BackupIssue, BackupStatus, Alert, Evaluation, HealthCheckReport

@pytest.mark.unit
def test_map_sql_service_from_str():
    service = mappers.map_sql_service("MSSQLSERVER")
    assert isinstance(service, SqlService)
    assert service.name == "MSSQLSERVER"
    assert service.status == "Unknown"

@pytest.mark.unit
def test_map_sql_service_from_dict():
    raw = {"Service": "SQLAgent", "DisplayName": "SQL Agent", "Status": "Running"}
    service = mappers.map_sql_service(raw)
    assert service.name == "SQLAgent"
    assert service.display_name == "SQL Agent"
    assert service.status == "Running"

@pytest.mark.unit
def test_map_disk_usage_from_dict():
    raw = {"Drive": "C:", "TotalGB": 100, "FreeGB": 50, "FreePercent": 50, "Issue": None}
    disk = mappers.map_disk_usage(raw)
    assert isinstance(disk, DiskUsage)
    assert disk.drive == "C:"
    assert disk.total_gb == 100
    assert disk.free_percent == 50

@pytest.mark.unit
def test_map_cpu_usage_with_samples():
    raw = {"sample": [{"timestamp": "2025-09-25T08:00:00", "percent": 42.5}]}
    cpu = mappers.map_cpu_usage(raw)
    assert isinstance(cpu, CpuUsage)
    assert len(cpu.samples) == 1
    assert cpu.samples[0].percent == 42.5

@pytest.mark.unit
def test_map_memory_usage_from_dict():
    raw = {"available_mb": 2048, "available_percent": 75.5, "physical_gb": 8}
    memory = mappers.map_memory_usage(raw)
    assert isinstance(memory, MemoryUsage)
    assert memory.available_mb == 2048
    assert memory.available_percent == 75.5
    assert memory.physical_gb == 8

@pytest.mark.unit
def test_map_backup_status_with_issue():
    raw = {
        "databases_offline": ["DB1"],
        "databases_missing_log_backup": [{"Database": "DB2", "DaysSinceLast": 5}],
        "note": "Some backups missing"
    }
    status = mappers.map_backup_status(raw)
    assert isinstance(status, BackupStatus)
    assert "DB1" in status.databases_offline
    assert isinstance(status.databases_missing_log_backup[0], BackupIssue)
    assert status.note == "Some backups missing"

@pytest.mark.unit
def test_map_alert_and_evaluation():
    raw_eval = {"severity": "Critical", "alerts": [{"level": "Warning", "message": "Low disk"}]}
    evaluation = mappers.map_evaluation(raw_eval)
    assert isinstance(evaluation, Evaluation)
    assert evaluation.severity == "Critical"
    assert evaluation.alerts[0].message == "Low disk"

@pytest.mark.unit
def test_map_failed_job_from_dict():
    raw = {"Job Name": "Nightly ETL", "Outcome": "Failed", "Last Run Status": "Error", "Message": "Disk full"}
    msg = mappers.map_failed_job(raw)
    assert "Job 'Nightly ETL' failed" in msg
    assert "Outcome: Failed" in msg
    assert "Status: Error" in msg
    assert "Message: Disk full" in msg

@pytest.mark.unit
def test_dict_to_healthcheck_end_to_end():
    raw_data = {
        "host": "SQLSERVER1",
        "sql_services": ["MSSQLSERVER"],
        "disk_usage": [{"Drive": "C:", "TotalGB": 500, "FreeGB": 100, "FreePercent": 20}],
        "cpu": {"sample": [{"timestamp": "2025-09-25T08:00:00", "percent": 35}]},
        "memory": {"available_mb": 1024, "available_percent": 80, "physical_gb": 16},
        "backups": {"note": "All good"},
        "failed_jobs": [{"JobName": "ETL", "Outcome": "Failed"}],
        "evaluation": {"severity": "Warning", "alerts": [{"level": "Info", "message": "Check ok"}]}
    }
    metadata = {"subject": "Health Check", "from": "monitor@company.com", "date": "2025-09-25"}
    report = mappers.dict_to_healthcheck("msg1", raw_data, metadata)

    assert isinstance(report, HealthCheckReport)
    assert report.host == "SQLSERVER1"
    assert report.services[0].name == "MSSQLSERVER"
    assert report.disks[0].drive == "C:"
    assert report.cpu.samples[0].percent == 35
    assert report.memory.available_mb == 1024
    assert report.backups.note == "All good"
    assert "ETL" in report.failed_jobs[0]
    assert report.evaluation.severity == "Warning"
    assert report.subject == "Health Check"

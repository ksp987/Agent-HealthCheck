# tests/test_parameter_engine.py

import pytest
from datetime import datetime
from src.core.models import (
    HealthCheckReport,
    SqlService,
    DiskUsage,
    CpuUsage,
    CpuSample,
    MemoryUsage,
    BackupStatus,
    BackupIssue,
    Evaluation,
    Alert,
)
from src.core.parameter_engine import ParameterEngine


def make_base_report() -> HealthCheckReport:
    """Helper: returns a clean baseline HealthCheckReport."""
    return HealthCheckReport(
        message_id="test123",
        subject="SQL Server Health Check Report",
        sender="monitor@test.com",
        date=str(datetime.utcnow()),
        host="TEST-SERVER",
        services=[SqlService(name="MSSQLSERVER", display_name="SQL Server", status="running")],
        disks=[DiskUsage(drive="C:", total_gb=100, free_gb=50, free_percent=50.0)],
        cpu=CpuUsage(samples=[CpuSample(timestamp=datetime.utcnow(), percent=10.0)], top_db_usage=[]),
        memory=MemoryUsage(available_mb=8000, available_percent=70.0, physical_gb=16, buffer_top_db=[]),
        backups=BackupStatus(databases_offline=[], databases_missing_log_backup=[], note=""),
        failed_jobs=[],
        evaluation=Evaluation(severity="info", alerts=[]),
    )


def test_clean_report_gives_info():
    report = make_base_report()
    engine = ParameterEngine(report)
    result = engine.evaluate()
    assert result.severity == "info"
    assert result.alerts == []


def test_disk_low_space_triggers_warning_and_critical():
    report = make_base_report()
    report.disks = [
        DiskUsage(drive="C:", total_gb=100, free_gb=19, free_percent=19.0),  # warning
        DiskUsage(drive="D:", total_gb=100, free_gb=10, free_percent=10.0),  # critical
    ]
    engine = ParameterEngine(report)
    result = engine.evaluate()

    levels = [a.level for a in result.alerts]
    assert "warning" in levels
    assert "critical" in levels
    assert result.severity == "critical"


def test_service_not_running_triggers_critical():
    report = make_base_report()
    report.services[0].status = "stopped"
    engine = ParameterEngine(report)
    result = engine.evaluate()

    assert result.severity == "critical"
    assert any("stopped" in a.message for a in result.alerts)


def test_backup_issue_triggers_warning():
    report = make_base_report()
    report.backups.databases_missing_log_backup = [
        BackupIssue(database="SalesDB", days_since_last=5, last_full_backup="2025-09-01"),
    ]
    engine = ParameterEngine(report)
    result = engine.evaluate()

    assert result.severity == "warning"
    assert any("SalesDB" in a.message for a in result.alerts)


def test_offline_db_triggers_critical():
    report = make_base_report()
    report.backups.databases_offline = ["FinanceDB"]
    engine = ParameterEngine(report)
    result = engine.evaluate()

    assert result.severity == "critical"
    assert any("FinanceDB" in a.message for a in result.alerts)


def test_failed_job_triggers_warning():
    report = make_base_report()
    report.failed_jobs = ["Nightly ETL"]
    engine = ParameterEngine(report)
    result = engine.evaluate()

    assert result.severity == "warning"
    assert any("Nightly ETL" in a.message for a in result.alerts)

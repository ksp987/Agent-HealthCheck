# src/core/mappers.py

from typing import Dict, Any
from datetime import datetime
from src.core.models import (
    HealthCheckReport, SqlService, DiskUsage, CpuSample, CpuUsage,
    MemoryUsage, BackupIssue, BackupStatus, Alert, Evaluation
)

def dict_to_healthcheck(msg_id: str, data: Dict[str, Any], metadata: Dict[str, Any]) -> HealthCheckReport:
    return HealthCheckReport(
        message_id=msg_id,
        subject=metadata.get("subject", ""),
        sender=metadata.get("from", ""),
        date=metadata.get("date", ""),
        host=data.get("host", ""),
        services=[SqlService(**s) for s in data.get("sql_services", [])],
        disks=[DiskUsage(**d) for d in data.get("disk_usage", [])],
        cpu=CpuUsage(
            samples=[
                CpuSample(
                    timestamp=datetime.fromisoformat(s["timestamp"]),
                    percent=s["percent"],
                )
                for s in data.get("cpu", {}).get("sample", [])
            ],
            top_db_usage=data.get("cpu", {}).get("top_db_usage", []),
        ),
        memory=MemoryUsage(
            available_mb=data["memory"]["available_MB"],
            available_percent=data["memory"]["available_percent"],
            physical_gb=data["memory"]["physical_GB"],
            buffer_top_db=data["memory"]["buffer_top_db"],
        ),
        backups=BackupStatus(
            databases_offline=data["backups"].get("databases_offline", []),
            databases_missing_log_backup=[
                BackupIssue(
                    database=b["Database"],
                    days_since_last=b["DaysSinceLast"],
                    last_full_backup=b["LastFullBackup"],
                )
                for b in data["backups"].get("databases_missing_log_backup", [])
            ],
            note=data["backups"].get("note", ""),
        ),
        failed_jobs=data.get("failed_jobs", []),
        evaluation=Evaluation(
            severity=data["evaluation"]["severity"],
            alerts=[Alert(**a) for a in data["evaluation"]["alerts"]],
        ),
    )

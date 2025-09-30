# src/core/mappers.py

from typing import Dict, Any
from datetime import datetime
from src.core.models import (
    HealthCheckReport, SqlService, DiskUsage, CpuSample, CpuUsage,
    MemoryUsage, BackupIssue, BackupStatus, Alert, Evaluation
)

# ---------------- Helpers ----------------
def safe_int(val, default=0):
    if isinstance(val, list) and val:
        val = val[0]
    try:
        return int(val)
    except Exception:
        return default

def safe_str(val, default=""):
    if isinstance(val, list) and val:
        val = val[0]
    if val is None:
        return default
    return str(val)

def safe_float(val, default=0.0):
    if isinstance(val, list) and val:
        val = val[0]
    try:
        return float(val)
    except Exception:
        return default


# ---------------- SQL Services ----------------
def map_sql_service(raw: Any) -> SqlService:
    if isinstance(raw, str):
        return SqlService(name=raw, display_name=raw, status="Unknown")

    if isinstance(raw, list):
        if raw and isinstance(raw[0], str):
            return SqlService(name=raw[0], display_name=raw[0], status="Unknown")
        return SqlService(name=str(raw), display_name=str(raw), status="Unknown")

    if isinstance(raw, dict):
        return SqlService(
            name=safe_str(raw.get("Service") or raw.get("name")),
            display_name=safe_str(raw.get("DisplayName") or raw.get("display_name")),
            status=safe_str(raw.get("Status") or raw.get("status"), "Unknown"),
        )

    return SqlService(name=str(raw), display_name=str(raw), status="Unknown")


# ---------------- Disk Usage ----------------
def map_disk_usage(raw: Any) -> DiskUsage:
    if isinstance(raw, dict):
        return DiskUsage(
            drive=safe_str(raw.get("Drive") or raw.get("drive")),
            total_gb=safe_float(raw.get("TotalGB") or raw.get("total_gb")),
            free_gb=safe_float(raw.get("FreeGB") or raw.get("free_gb")),
            free_percent=safe_float(raw.get("FreePercent") or raw.get("free_percent")),
            issue=raw.get("Issue") or raw.get("issue"),
        )

    if isinstance(raw, list) and len(raw) == 2:
        return DiskUsage(
            drive=safe_str(raw[0]),
            total_gb=0.0,
            free_gb=0.0,
            free_percent=safe_float(raw[1]),
        )

    return DiskUsage(drive=safe_str(raw), total_gb=0, free_gb=0, free_percent=0)


# ---------------- CPU Usage ----------------
def map_cpu_sample(raw: Dict[str, Any]) -> CpuSample:
    ts = raw.get("timestamp") or raw.get("Timestamp")
    try:
        timestamp = datetime.fromisoformat(ts) if ts else datetime.utcnow()
    except Exception:
        timestamp = datetime.utcnow()

    return CpuSample(
        timestamp=timestamp,
        percent=safe_float(raw.get("percent") or raw.get("Percent")),
    )

def map_cpu_usage(raw: Dict[str, Any]) -> CpuUsage:
    samples = []
    for s in raw.get("sample", []):
        if isinstance(s, dict):  # skip bad shapes
            samples.append(map_cpu_sample(s))
    return CpuUsage(
        samples=samples,
        top_db_usage=raw.get("top_db_usage", []),
    )


# ---------------- Memory Usage ----------------
def map_memory_usage(raw: Dict[str, Any]) -> MemoryUsage:
    return MemoryUsage(
        available_mb=safe_int(raw.get("available_MB") or raw.get("available_mb")),
        available_percent=safe_float(raw.get("available_percent")),
        physical_gb=safe_int(raw.get("physical_GB") or raw.get("physical_gb")),
        buffer_top_db=raw.get("buffer_top_db", []),
    )


# ---------------- Backup Issues ----------------
def map_backup_issue(raw: Dict[str, Any]) -> BackupIssue:
    return BackupIssue(
        database=safe_str(raw.get("Database") or raw.get("database")),
        days_since_last=safe_int(raw.get("DaysSinceLast") or raw.get("days_since_last")),
        last_full_backup=safe_str(raw.get("LastFullBackup") or raw.get("last_full_backup")),
    )

def map_backup_status(raw: Dict[str, Any]) -> BackupStatus:
    return BackupStatus(
        databases_offline=raw.get("databases_offline", []),
        databases_missing_log_backup=[
            map_backup_issue(b) for b in raw.get("databases_missing_log_backup", [])
        ],
        note=safe_str(raw.get("note")),
    )


# ---------------- Alerts / Evaluation ----------------
def map_alert(raw: Dict[str, Any]) -> Alert:
    return Alert(
        level=safe_str(raw.get("Level") or raw.get("level")),
        message=safe_str(raw.get("Message") or raw.get("message")),
    )

def map_evaluation(raw: Dict[str, Any]) -> Evaluation:
    return Evaluation(
        severity=safe_str(raw.get("severity")),
        alerts=[map_alert(a) for a in raw.get("alerts", [])],
    )


# ---------------- Failed Jobs ----------------
def map_failed_job(raw: Any) -> str:
    if isinstance(raw, list):
        return "; ".join([map_failed_job(j) for j in raw])

    if isinstance(raw, dict):
        job_name = raw.get("Job Name") or raw.get("JobName") or "Unknown Job"
        outcome = raw.get("Outcome")
        status = raw.get("Last Run Status") or raw.get("Status")
        message = raw.get("Message")

        parts = [f"Job '{job_name}' failed"]
        if outcome is not None:
            parts.append(f"Outcome: {outcome}")
        if status:
            parts.append(f"Status: {status}")
        if message:
            parts.append(f"Message: {message}")

        return " | ".join(parts)

    return str(raw)


# ---------------- Health Check Report ----------------
def dict_to_healthcheck(msg_id: str, data: Dict[str, Any], metadata: Dict[str, Any]) -> HealthCheckReport:
    return HealthCheckReport(
        message_id=msg_id,
        subject=metadata.get("subject", ""),
        sender=metadata.get("from", ""),
        date=metadata.get("date", ""),
        host=data.get("host", ""),
        services=[map_sql_service(s) for s in data.get("sql_services", [])],
        disks=[map_disk_usage(d) for d in data.get("disk_usage", [])],
        cpu=map_cpu_usage(data.get("cpu", {})),
        memory=map_memory_usage(data.get("memory", {})),
        backups=map_backup_status(data.get("backups", {})),
        failed_jobs=[map_failed_job(j) for j in data.get("failed_jobs", [])],
        evaluation=map_evaluation(data.get("evaluation", {})),
    )

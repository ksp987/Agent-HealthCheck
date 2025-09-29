# src/core/models.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class SqlService:
    name: str
    display_name: str
    status: str


@dataclass
class DiskUsage:
    drive: str
    total_gb: float
    free_gb: float
    free_percent: float
    issue: Optional[str] = None


@dataclass
class CpuSample:
    timestamp: datetime
    percent: float


@dataclass
class CpuUsage:
    samples: List[CpuSample]
    top_db_usage: List[Dict[str, float]]


@dataclass
class MemoryUsage:
    available_mb: int
    available_percent: float
    physical_gb: int
    buffer_top_db: List[Dict[str, float]]


@dataclass
class BackupIssue:
    database: str
    days_since_last: int
    last_full_backup: str


@dataclass
class BackupStatus:
    databases_offline: List[str]
    databases_missing_log_backup: List[BackupIssue]
    note: str


@dataclass
class Alert:
    level: str
    message: str


@dataclass
class Evaluation:
    severity: str
    alerts: List[Alert]


@dataclass
class HealthCheckReport:
    message_id: str
    subject: str #gmail subject
    sender: str
    date: str
    host: str
    services: List[SqlService]
    disks: List[DiskUsage]
    cpu: CpuUsage
    memory: MemoryUsage
    backups: BackupStatus
    failed_jobs: List[str]
    evaluation: Evaluation

# src/core/parameter_engine.py

import logging
from typing import List
from src.core.models import (
    HealthCheckReport,
    Evaluation,
    Alert,
    DiskUsage,
    SqlService,
    BackupStatus,
)

logger = logging.getLogger(__name__)


class ParameterEngine:
    """
    Applies post-processing rules to a HealthCheckReport.
    Evaluates severity based on disk usage, services, backups, and failed jobs.
    """

    def __init__(self, report: HealthCheckReport):
        self.report = report
        self.alerts: List[Alert] = []

    def evaluate(self) -> Evaluation:
        """Run all checks and return an Evaluation object."""
        self._check_disk_usage()
        self._check_sql_services()
        self._check_backups()
        self._check_failed_jobs()

        severity = self._derive_severity()
        return Evaluation(severity=severity, alerts=self.alerts)

    # ------------------ Individual Checks ------------------

    def _check_disk_usage(self):
        for disk in self.report.disks:
            if disk.free_percent < 15:
                msg = f"CRITICAL: Drive {disk.drive} has only {disk.free_percent:.2f}% free space."
                self._add_alert("critical", msg)
            elif disk.free_percent < 20:
                msg = f"WARNING: Drive {disk.drive} has {disk.free_percent:.2f}% free space."
                self._add_alert("warning", msg)

    def _check_sql_services(self):
        for svc in self.report.services:
            if svc.status.lower() != "running":
                msg = f"CRITICAL: SQL Service '{svc.display_name}' ({svc.name}) is {svc.status}."
                self._add_alert("critical", msg)

    def _check_backups(self):
        backups: BackupStatus = self.report.backups
        for issue in backups.databases_missing_log_backup:
            if issue.days_since_last > 2:
                msg = (
                    f"WARNING: Database {issue.database} has no recent log backup "
                    f"(last full backup: {issue.last_full_backup})."
                )
                self._add_alert("warning", msg)

        for db in backups.databases_offline:
            msg = f"CRITICAL: Database {db} is offline."
            self._add_alert("critical", msg)

    def _check_failed_jobs(self):
        for job in self.report.failed_jobs:
            msg = f"WARNING: SQL Agent job '{job}' has failed."
            self._add_alert("warning", msg)

    # ------------------ Helpers ------------------

    def _add_alert(self, level: str, message: str):
        logger.warning(f"{level.upper()}: {message}")
        self.alerts.append(Alert(level=level, message=message))

    def _derive_severity(self) -> str:
        levels = [a.level for a in self.alerts]
        if "critical" in levels:
            return "critical"
        elif "warning" in levels:
            return "warning"
        return "info"

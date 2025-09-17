# src/ai_agent/parameter_engine.py

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ParameterEngine:
    """
    Applies post-processing rules to health check insights.
    Evaluates severity based on disk usage, backups, and failed jobs.
    """

    def __init__(self, insights: Dict):
        self.insights = insights
        self.alerts: List[Dict] = []

    def evaluate(self) -> Dict:
        """
        Run all rules and return structured result:
        {
          "severity": "Critical/Warning/OK",
          "alerts": [ ... list of triggered rules ... ]
        }
        """
        self._check_disk_usage()
        self._check_backups()
        self._check_failed_jobs()

        # Decide severity
        if any(a["level"] == "Critical" for a in self.alerts):
            severity = "Critical"
        elif any(a["level"] == "Warning" for a in self.alerts):
            severity = "Warning"
        else:
            severity = "OK"

        result = {
            "severity": severity,
            "alerts": self.alerts,
        }

        logger.info("RuleEngine evaluation complete: %s", result)
        return result

    # -------------------- Rules --------------------

    def _check_disk_usage(self):
        for disk in self.insights.get("disk_usage", []):
            if isinstance(disk, dict):
                if disk.get("alert"):
                    self.alerts.append({
                        "level": "Critical",
                        "message": f"Drive {disk.get('name', 'Unknown')} low free space ({disk.get('free_pct', '?')}%)"
                    })
            elif isinstance(disk, str):
                self.alerts.append({
                    "level": "Critical",
                    "message": disk
                })

    def _check_backups(self):
        for db in self.insights.get("backups", []):
            if isinstance(db, dict):
                if db.get("alert"):
                    self.alerts.append({
                        "level": "Warning",
                        "message": f"Database {db.get('database', 'Unknown')} backup issue: {db.get('status', 'Unknown')}"
                    })
            elif isinstance(db, str):
                # Already a string alert
                self.alerts.append({
                    "level": "Warning",
                    "message": db
                })
    
    def _check_failed_jobs(self):
        for job in self.insights.get("failed_jobs", []):
            if isinstance(job, dict):
                self.alerts.append({
                    "level": "Critical",
                    "message": f"Job {job.get('job_name', 'Unknown')} failed: {job.get('message', 'No details')}"
                })
            elif isinstance(job, str):
                self.alerts.append({
                    "level": "Critical",
                    "message": job
                })
        
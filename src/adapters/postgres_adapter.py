import logging
import os
import psycopg2
import json
from typing import List, Dict
from src.core.ports.storage_port import StoreResultsPort

logger = logging.getLogger(__name__)

class PostgresAdapter(StoreResultsPort):
    """
    Adapter for saving email results into Postgres/Azure SQL.
    """

    def __init__(self, conn_str_env: str = "AZURE_SQL_CONN"):
        self.conn_str = os.getenv(conn_str_env)
        if not self.conn_str:
            raise ValueError(f"Missing connection string in env: {conn_str_env}")

    def save_results(self, results: List[Dict]) -> None:
        try:
            with psycopg2.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    for r in results:
                        cur.execute(
                            """
                            INSERT INTO healthcheck_emails (message_id, subject, sender, date, insights, evaluation)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (message_id) DO NOTHING;
                            """,
                            (
                                r["id"],
                                r.get("subject"),
                                r.get("from"),
                                r.get("date"),
                                json.dumps(r.get("insights")),
                                json.dumps(r.get("evaluation", {}))
                            )
                        )
                conn.commit()
            logger.info("Saved %d results to Postgres", len(results))
        except Exception as e:
            logger.error("Failed to save results to Postgres: %s", str(e))
            raise

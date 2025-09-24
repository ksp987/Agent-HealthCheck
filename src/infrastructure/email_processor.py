# src/infrastructure/email_processor.py

import logging
import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from pytz import timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmailProcessor:
    """
    Infrastructure service for working with Gmail + OpenAI.
    Responsibilities:
      - Query Gmail for recent messages by subject
      - Decode email bodies (plain or HTML)
      - Fetch metadata (subject, from, date)
      - Run bodies through Azure OpenAI to produce structured insights
    """

    def __init__(self, service: Any, user_id: str = "me", tz_name: str = "Australia/Melbourne"):
        self.service = service
        self.user_id = user_id
        self.tz = timezone(tz_name)

        # Initialize OpenAI client from env
        self.client = OpenAI(
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # e.g., "gpt-4.1"

    # -------------------- Gmail Fetching --------------------
    def _epoch_seconds_now_minus(self, minutes: int) -> int:
        now_local = datetime.now(self.tz)
        since = now_local - timedelta(minutes=minutes)
        return int(since.timestamp())

    def _build_query(self, since_epoch: int, subject: str) -> str:
        return f"after:{since_epoch} subject:\"{subject}\""

    def find_recent_messages(self, minutes: int, subject: str, max_results: int = 50) -> List[Dict]:
        """
        Return message stubs: [{'id': '...', 'threadId': '...'}, ...]
        """
        since_epoch = self._epoch_seconds_now_minus(minutes)
        q = self._build_query(since_epoch, subject)

        req = self.service.users().messages().list(
            userId=self.user_id,
            q=q,
            maxResults=max_results,
        )
        resp = req.execute()
        return resp.get("messages", [])

    def _decode_body(self, payload: Dict, prefer_html: bool = False) -> str:
        def decode(data):
            return base64.urlsafe_b64decode(data.encode("UTF-8")).decode("UTF-8")

        # Single-part
        if "data" in payload.get("body", {}):
            return decode(payload["body"]["data"]).strip()

        # Multipart
        for part in payload.get("parts", []):
            mime = part.get("mimeType", "")
            if (prefer_html and mime == "text/html") or (not prefer_html and mime == "text/plain"):
                data = part["body"].get("data")
                if data:
                    return decode(data).strip()
        return ""

    def fetch_message_body(self, msg_id: str, prefer_html: bool = False) -> str:
        msg = self.service.users().messages().get(
            userId=self.user_id,
            id=msg_id,
            format="full",
        ).execute()

        payload = msg.get("payload", {})
        return self._decode_body(payload, prefer_html=prefer_html)

    def fetch_message_metadata(self, msg_id: str) -> Dict:
        msg = self.service.users().messages().get(
            userId=self.user_id,
            id=msg_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        return {
            "subject": headers.get("Subject"),
            "from": headers.get("From"),
            "date": headers.get("Date"),
        }

    # -------------------- Azure OpenAI Insights --------------------
    def extract_insights(self, body: str) -> Dict:
        if not body.strip():
            return {"error": "empty body"}

        prompt = f"""
        You are a monitoring assistant. Parse the following SQL Server health check email 
        and extract issues/metrics as JSON with keys:
        host, sql_services, disk_usage, cpu, memory, backups, failed_jobs, alerts.

        Email:
        {body}
        """

        try:
            resp = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            raw_content = resp.choices[0].message.content
            return json.loads(raw_content)
        except Exception as e:
            logger.error("Failed to parse JSON from OpenAI: %s", str(e))
            return {"error": f"Failed to parse JSON: {str(e)}"}

    # -------------------- End-to-End Pipeline --------------------
    def process_recent_messages(self, minutes: int, subject: str) -> List[Dict]:
        """
        Find all messages in last X minutes filtered by subject,
        decode bodies, fetch metadata, and extract insights.
        Returns list of dicts with {id, subject, from, date, insights}.
        """
        messages = self.find_recent_messages(minutes=minutes, subject=subject)
        results = []

        for msg in messages:
            msg_id = msg["id"]
            try:
                body = self.fetch_message_body(msg_id)
                insights = self.extract_insights(body)
                metadata = self.fetch_message_metadata(msg_id)

                results.append({"id": msg_id, "insights": insights, **metadata})
            except Exception as e:
                logger.error("Failed to process message %s: %s", msg_id, str(e))

        logger.info("Processed %d messages for subject '%s'", len(results), subject)
        return results


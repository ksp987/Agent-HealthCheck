# src/ai_agent/email_processor.py

import logging
import base64
from datetime import datetime, timedelta
from typing import List, Dict
import json

from googleapiclient.discovery import Resource
from pytz import timezone
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

# Setup Azure OpenAI client from environment
client = OpenAI(
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # "gpt-4.1"


class EmailProcessor:
    """
    Process recent Gmail messages:
      - Search messages within last X minutes (subject required)
      - Extract plain-text or HTML bodies
      - Run through Azure OpenAI to produce structured insights
    """

    def __init__(self, service: Resource, user_id: str = "me", tz_name: str = "Australia/Melbourne"):
        self.service = service
        self.user_id = user_id
        self.tz = timezone(tz_name)

    # -------------------- Gmail Fetching --------------------
    def _epoch_seconds_now_minus(self, minutes: int) -> int:
        now_local = datetime.now(self.tz)
        since = now_local - timedelta(minutes=minutes)
        return int(since.timestamp())

    def _build_query(self, since_epoch: int, subject: str) -> str:
        # Subject is mandatory
        return f"after:{since_epoch} subject:\"{subject}\""

    def find_recent_messages(self, minutes: int, subject: str, max_results: int = 50) -> List[Dict]:
        """
        Returns a list of message stubs: [{'id': '...', 'threadId': '...'}, ...]
        Always filtered by subject.
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
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        return {
            "subject": headers.get("Subject"),
            "from": headers.get("From"),
            "date": headers.get("Date"),
        }

    # -------------------- Azure OpenAI Insights --------------------
    def extract_insights(self, body: str) -> Dict:
        """
        Uses Azure OpenAI to parse health check email body into structured JSON.
        """
        if not body.strip():
            return {"error": "empty body"}

        prompt = f"""
        You are a monitoring assistant. Parse the following SQL Server health check email 
        and extract issues/metrics as JSON with keys:
        host, sql_services, disk_usage, cpu, memory, backups, failed_jobs, alerts.

        Email:
        {body}
        """

        resp = client.chat.completions.create(
            model=deployment,  
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw_content = resp.choices[0].message.content
        try:
            return json.loads(raw_content)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}", "raw": raw_content}
    

    # -------------------- End-to-End Pipeline --------------------
    def process_recent_messages(self, minutes: int, subject: str) -> List[Dict]:
        """
        Find all messages in last X minutes filtered by subject,
        decode bodies, and extract insights.
        Returns list of structured JSON dicts (one per email).
        """
        messages = self.find_recent_messages(minutes=minutes, subject=subject)
        results = []

        for msg in messages:
            msg_id = msg["id"]
            body = self.fetch_message_body(msg_id)
            insights = self.extract_insights(body)
            results.append({"id": msg_id, "insights": insights})

        logger.info("Processed %d messages for subject '%s'", len(results), subject)
        return results

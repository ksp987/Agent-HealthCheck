import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from googleapiclient.discovery import Resource
from pytz import timezone

logger = logging.getLogger(__name__)


class EmailFetcher:
    """
    Thin wrapper around the Gmail API `users().messages().list()` and `.get()`.
    Keeps time logic + pagination in one place.
    """

    def __init__(
        self,
        service: Resource,
        user_id: str = "me",
        tz_name: str = "Australia/Melbourne",
    ) -> None:
        self.service = service
        self.user_id = user_id
        self.tz = timezone(tz_name)

    def _epoch_seconds_now_minus(self, minutes: int) -> int:
        now_local = datetime.now(self.tz)
        since = now_local - timedelta(minutes=minutes)
        return int(since.timestamp())

    def _build_query(
        self,
        since_epoch: int,
        subject: Optional[str] = None,
        extra_query: Optional[str] = None,
    ) -> str:
        parts = [f"after:{since_epoch}"]
        if subject:
            # Quote the subject so spaces work as expected
            parts.append(f"subject:\"{subject}\"")
        if extra_query:
            parts.append(extra_query.strip())
        return " ".join(parts)

    def list_messages_since(
        self,
        minutes: int,
        subject: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        include_spam_trash: bool = False,
        max_results: Optional[int] = None,
        extra_query: Optional[str] = None,
    ) -> List[Dict]:
        """
        Returns a list of message stubs: [{'id': '...', 'threadId': '...'}, ...]
        Use `get_message()` to fetch bodies/headers when needed.
        """
        since_epoch = self._epoch_seconds_now_minus(minutes)
        q = self._build_query(since_epoch, subject=subject, extra_query=extra_query)

        logger.info("Gmail search query: %s", q)

        all_msgs: List[Dict] = []
        page_token = None

        while True:
            req = (
                self.service.users()
                .messages()
                .list(
                    userId=self.user_id,
                    q=q,
                    labelIds=label_ids,
                    includeSpamTrash=include_spam_trash,
                    pageToken=page_token,
                    maxResults=max_results,  # None means API default (<=100)
                )
            )
            resp = req.execute()
            msgs = resp.get("messages", [])
            all_msgs.extend(msgs)

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        logger.info("Fetched %d messages.", len(all_msgs))
        return all_msgs

    def get_message(
        self,
        msg_id: str,
        fmt: str = "metadata",
        metadata_headers: Optional[List[str]] = None,
    ) -> Dict:
        """
        Fetch a single message. `fmt` can be: 'full', 'metadata', 'raw', 'minimal'.
        """
        req = (
            self.service.users()
            .messages()
            .get(
                userId=self.user_id,
                id=msg_id,
                format=fmt,
                metadataHeaders=metadata_headers or ["Subject", "From", "Date"],
            )
        )
        return req.execute()

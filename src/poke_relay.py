"""Push calendar events to teammates' Poke via webhooks or direct API."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

POKE_API_BASE = "https://poke.com/api/v1"
POKE_WEBHOOK_URL = "https://poke.com/api/v1/inbound/webhook"


def _calendar_message(event: dict[str, Any]) -> str:
    """Format calendar event as a natural-language message for Poke."""
    return (
        f"Add this to my calendar: {event.get('title', 'Meeting')} "
        f"from {event.get('start', '')} to {event.get('end', '')}. "
        f"Attendees: {', '.join(event.get('attendees', []) or ['team'])}."
    )


def push_via_webhook(
    webhook_url: str,
    webhook_token: str,
    event: dict[str, Any],
) -> bool:
    """
    Send a calendar invite via Poke webhook.
    Teammate creates webhook at poke.com/kitchen with action "Add to my calendar".
    """
    try:
        payload = {
            "event": "team_brain_calendar_invite",
            "title": event.get("title", ""),
            "start": event.get("start", ""),
            "end": event.get("end", ""),
            "attendees": event.get("attendees", []),
            "message": _calendar_message(event),
        }
        headers = {
            "Authorization": f"Bearer {webhook_token}",
            "Content-Type": "application/json",
        }
        url = webhook_url.strip() if webhook_url and webhook_url.startswith("http") else POKE_WEBHOOK_URL
        resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        if resp.status_code >= 400:
            logger.warning("Poke webhook failed: %s %s", resp.status_code, resp.text)
            return False
        return True
    except Exception as e:
        logger.exception("Poke webhook error: %s", e)
        return False


def push_via_api_key(api_key: str, event: dict[str, Any]) -> bool:
    """
    Send a message directly to a teammate's Poke.
    Uses their API key from poke.com/kitchen/api-keys.
    """
    if not api_key or not api_key.startswith("pk_"):
        return False
    try:
        message = _calendar_message(event)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # Poke API: POST /messages (try common patterns)
        for path in ("/messages", "/agent/message"):
            resp = httpx.post(
                f"{POKE_API_BASE}{path}",
                json={"message": message},
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code < 400:
                return True
            if resp.status_code != 404:
                logger.warning("Poke API %s: %s", path, resp.status_code)
        return False
    except Exception as e:
        logger.exception("Poke API error: %s", e)
        return False


def push_calendar_invite_to_poke(
    webhook_url: str,
    webhook_token: str,
    event: dict[str, Any],
    api_key: str = "",
) -> bool:
    """Push calendar invite to a teammate. Tries webhook first, then API key."""
    if webhook_url and webhook_token:
        if push_via_webhook(webhook_url, webhook_token, event):
            return True
    if api_key:
        return push_via_api_key(api_key, event)
    return False

"""
Send calendar events to each teammate's Poke via HTTP.
Uses JWT tokens (from poke login) or pk_ API keys.
"""

import httpx

POKE_API = "https://poke.com/api/v1/inbound/api-message"


def send_to_poke(api_key: str, title: str, start: str, end: str) -> tuple[bool, str]:
    """
    Send a calendar add request to one person's Poke.
    api_key: JWT (eyJ...) or pk_ - JWT works, pk_ often returns 401.
    Returns (success, error_message).
    """
    if not api_key or len(api_key) < 20:
        return False, "invalid key"
    msg = f"Add this to my calendar: {title} from {start} to {end}"
    try:
        r = httpx.post(
            POKE_API,
            json={"message": msg},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        if r.status_code >= 400:
            return False, f"HTTP {r.status_code}: {r.text[:150]}"
        return True, ""
    except Exception as e:
        return False, str(e)


def send_to_all_pokes(
    api_keys: list[str], title: str, start: str, end: str
) -> list[tuple[str, bool, str]]:
    """Send to every Poke. Returns list of (key_prefix, success, error)."""
    results = []
    for key in api_keys:
        prefix = key[:20] + "..." if len(key) > 20 else key
        ok, err = send_to_poke(key, title, start, end)
        results.append((prefix, ok, err))
    return results

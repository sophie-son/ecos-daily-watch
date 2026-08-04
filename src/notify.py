"""
notify.py

Sends a formatted message to a Discord channel via webhook.
No auth token needed -- the webhook URL itself is the credential,
which is why it's passed in as a secret rather than hardcoded.
"""

import json
import urllib.request
import urllib.error


def send_discord_message(webhook_url: str, content: str) -> None:
    """
    Posts `content` to the given Discord webhook URL.
    Raises RuntimeError if the request fails.
    """
    payload = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            # Discord sits behind Cloudflare, which blocks the default
            # urllib identifier ("Python-urllib/3.x") as a bot signature
            # -- this shows up as a 403 / "error code: 1010". A normal
            # User-Agent string avoids that entirely.
            "User-Agent": "ecos-daily-watch/1.0 (personal automation script)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.status
            if status not in (200, 204):
                raise RuntimeError(f"Discord webhook returned unexpected status: {status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Discord webhook failed: {e.code} {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Discord webhook request failed: {e}") from e

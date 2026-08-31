"""
main.py

Entry point run daily by GitHub Actions.
Fetches ECOS data, formats a Discord message, and sends it.

Required environment variables (set as GitHub Actions secrets, never
hardcoded here):
    ECOS_API_KEY
    DISCORD_WEBHOOK_URL
"""

from __future__ import annotations

import os
import sys

from src.fetch import fetch_key_stats
from src.notify import send_discord_message
from src.history import append_today
from src.detect import check_deviation


def format_message(metrics: list[dict]) -> str:
    lines = ["**오늘의 경제 지표 (한국은행 ECOS)**", ""]
    for m in metrics:
        date_str = m["date"] or ""
        if len(date_str) == 8:
            date_display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        else:
            date_display = date_str
        value = m["value"]
        value_display = f"{value:.2f}" if isinstance(value, (int, float)) else value

        flag_marker = "🔴 " if m.get("flagged") else ""
        change_note = f" ({m['change_display']} vs 전일)" if m.get("change_display") else ""

        lines.append(
            f"- {flag_marker}{m['name_kr']} ({m['label']}): **{value_display}{m['unit']}**{change_note} ({date_display} 기준)"
        )
    return "\n".join(lines)


def main():
    api_key = os.environ.get("ECOS_API_KEY")
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not api_key or not webhook_url:
        print("ERROR: ECOS_API_KEY and DISCORD_WEBHOOK_URL must be set.")
        sys.exit(1)

    try:
        metrics = fetch_key_stats(api_key)
        metrics = check_deviation(metrics)
        message = format_message(metrics)
        send_discord_message(webhook_url, message)
        append_today(metrics)
        print("Sent successfully:")
        print(message)
    except Exception as e:
        error_message = f"⚠️ Daily ECOS check failed: {type(e).__name__}: {e}"
        print(error_message)
        try:
            send_discord_message(webhook_url, error_message)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
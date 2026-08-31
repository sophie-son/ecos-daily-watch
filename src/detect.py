"""
detect.py

Flags a metric as "notable" when today's value has moved more than a
calibrated threshold compared to the most recent previous day.

Thresholds were set by computing real day-to-day volatility from
data/history.csv once ~3 weeks of real data existed, not guessed in
advance. A moving-average comparison was tested and rejected -- it
produced large deviations during ordinary trending periods (KOSPI
rallied ~10% over this window), which would flag too often to be
useful. See README for the full reasoning.
"""

from __future__ import annotations

import csv
import os

from src.history import HISTORY_PATH

THRESHOLDS = {
    "USD/KRW": {"column": "usd_krw", "threshold": 1.0, "mode": "percent"},
    "KOSPI": {"column": "kospi", "threshold": 5.0, "mode": "percent"},
    "3Y Treasury Yield": {"column": "treasury_3y", "threshold": 0.10, "mode": "points"},
}


def _load_history() -> list[dict]:
    if not os.path.isfile(HISTORY_PATH):
        return []
    with open(HISTORY_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_deviation(metrics: list[dict]) -> list[dict]:
    history = _load_history()

    for m in metrics:
        rule = THRESHOLDS.get(m["label"])
        m["flagged"] = False
        m["change_display"] = None

        if not rule or not history:
            continue

        try:
            previous_value = float(history[-1][rule["column"]])
            today_value = float(m["value"])
        except (KeyError, TypeError, ValueError):
            continue

        if rule["mode"] == "percent":
            if previous_value == 0:
                continue
            change = (today_value - previous_value) / previous_value * 100
            m["change_display"] = f"{change:+.2f}%"
            m["flagged"] = abs(change) >= rule["threshold"]
        else:
            change = today_value - previous_value
            m["change_display"] = f"{change:+.2f}pt"
            m["flagged"] = abs(change) >= rule["threshold"]

    return metrics
"""
history.py

Appends each day's fetched metrics to a CSV file living in the repo,
building up a running history. This is the "memory" the anomaly
detection step (planned next) will compare each new day against.
"""

import csv
import os

HISTORY_PATH = "data/history.csv"
FIELDNAMES = ["date", "usd_krw", "kospi", "treasury_3y"]

LABEL_TO_COLUMN = {
    "USD/KRW": "usd_krw",
    "KOSPI": "kospi",
    "3Y Treasury Yield": "treasury_3y",
}


def append_today(metrics: list[dict]) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)

    row = {"date": None}
    for m in metrics:
        column = LABEL_TO_COLUMN.get(m["label"])
        if column:
            row[column] = m["value"]
            row["date"] = _format_date(m["date"])

    if row["date"] is None:
        raise RuntimeError("Could not determine date for history row")

    if _date_already_recorded(row["date"]):
        print(f"History already has an entry for {row['date']}, skipping append.")
        return

    file_exists = os.path.isfile(HISTORY_PATH)
    with open(HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _format_date(date_str: str) -> str:
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


def _date_already_recorded(date_str: str) -> bool:
    if not os.path.isfile(HISTORY_PATH):
        return False
    with open(HISTORY_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return any(r["date"] == date_str for r in reader)